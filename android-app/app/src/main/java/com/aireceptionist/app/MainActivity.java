package com.aireceptionist.app;

import android.Manifest;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.media.AudioFormat;
import android.media.AudioManager;
import android.media.AudioRecord;
import android.media.MediaRecorder;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.Gravity;
import android.view.View;
import android.view.animation.AlphaAnimation;
import android.view.animation.Animation;
import android.view.animation.ScaleAnimation;
import android.view.animation.AnimationSet;
import android.widget.LinearLayout;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import com.aireceptionist.app.databinding.ActivityMainBinding;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import okhttp3.WebSocket;
import okhttp3.WebSocketListener;
import okio.ByteString;

/**
 * AI Receptionist — Creative Call Screen
 *
 * Design:
 *  • Dark ambient background with blue glow
 *  • Pulsing avatar ring (animated when active)
 *  • Live call timer
 *  • Chat bubble transcript (user = left blue, AI = right dark)
 *  • Large green call button + end/mute controls
 */
public class MainActivity extends AppCompatActivity {

    private static final String TAG = "AIReceptionist";
    private static final int PERM_REQUEST_CODE = 101;
    private static final int SAMPLE_RATE = 16000;
    private static final int CHANNEL_IN = AudioFormat.CHANNEL_IN_MONO;
    private static final int ENCODING = AudioFormat.ENCODING_PCM_16BIT;

    private ActivityMainBinding binding;
    private OkHttpClient httpClient;
    private WebSocket webSocket;
    private AudioRecord audioRecord;

    private final AtomicBoolean isRecording = new AtomicBoolean(false);
    private final AtomicBoolean isReceivingTts = new AtomicBoolean(false);
    private final AtomicBoolean isPlayingTts = new AtomicBoolean(false);
    private final AtomicBoolean isMuted = new AtomicBoolean(false);
    private final AtomicBoolean shouldEndCall = new AtomicBoolean(false);
    private final ByteArrayOutputStream ttsBuffer = new ByteArrayOutputStream();
    private android.media.MediaPlayer currentMediaPlayer;
    private long lastTtsEndTime = 0;

    private final ExecutorService executor = Executors.newCachedThreadPool();
    private final Handler uiHandler = new Handler(Looper.getMainLooper());

    // Call timer
    private int callSeconds = 0;
    private final Runnable timerTick = new Runnable() {
        @Override public void run() {
            if (callState == CallState.ACTIVE || callState == CallState.PROCESSING) {
                callSeconds++;
                int m = callSeconds / 60, s = callSeconds % 60;
                binding.tvCallTimer.setText(String.format("%02d:%02d", m, s));
                uiHandler.postDelayed(this, 1000);
            }
        }
    };

    // Pulse animation
    private Animation pulseAnim;
    private int msgCount = 0;

    private enum CallState { IDLE, CONNECTING, ACTIVE, PROCESSING, ENDING }
    private CallState callState = CallState.IDLE;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Full-screen immersive
        getWindow().setStatusBarColor(Color.parseColor("#060A12"));
        getWindow().setNavigationBarColor(Color.parseColor("#060A12"));

        binding = ActivityMainBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        httpClient = new OkHttpClient.Builder()
                .readTimeout(0, TimeUnit.MILLISECONDS)
                .pingInterval(10, TimeUnit.SECONDS)  // Aggressive ping to keep Render connection alive
                .build();

        buildPulseAnimation();

        // Call button
        binding.btnCall.setOnClickListener(v -> {
            if (callState == CallState.IDLE) startCallFlow();
        });

        // End call button
        binding.btnEndCall.setOnClickListener(v -> endCall());

        // Settings button
        binding.btnSettings.setOnClickListener(v ->
                startActivity(new Intent(this, SettingsActivity.class)));

        // Mute toggle (invisible FrameLayout parent)
        binding.btnMuteWrap.setOnClickListener(v -> toggleMute());

        updateUI(CallState.IDLE);
    }

    // ── Animations ─────────────────────────────────────────────────────────

    private void buildPulseAnimation() {
        ScaleAnimation scale = new ScaleAnimation(
                0.88f, 1.08f, 0.88f, 1.08f,
                Animation.RELATIVE_TO_SELF, 0.5f,
                Animation.RELATIVE_TO_SELF, 0.5f);
        scale.setDuration(900);
        scale.setRepeatMode(Animation.REVERSE);
        scale.setRepeatCount(Animation.INFINITE);

        AlphaAnimation alpha = new AlphaAnimation(0.4f, 1.0f);
        alpha.setDuration(900);
        alpha.setRepeatMode(Animation.REVERSE);
        alpha.setRepeatCount(Animation.INFINITE);

        pulseAnim = new AnimationSet(true);
        ((AnimationSet) pulseAnim).addAnimation(scale);
        ((AnimationSet) pulseAnim).addAnimation(alpha);
    }

    private void startPulse() {
        uiHandler.post(() -> binding.pulseRing.startAnimation(pulseAnim));
    }

    private void stopPulse() {
        uiHandler.post(() -> {
            binding.pulseRing.clearAnimation();
            binding.pulseRing.setAlpha(0.18f);
        });
    }

    // ── Call flow ───────────────────────────────────────────────────────────

    private void startCallFlow() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
                != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this,
                    new String[]{Manifest.permission.RECORD_AUDIO}, PERM_REQUEST_CODE);
        } else {
            connectAndStartCall();
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode,
                                           @NonNull String[] permissions,
                                           @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == PERM_REQUEST_CODE
                && grantResults.length > 0
                && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            connectAndStartCall();
        } else {
            showStatus("Microphone access denied");
        }
    }

    private String getServerUrl() {
        SharedPreferences prefs = getSharedPreferences("ai_receptionist_prefs", MODE_PRIVATE);
        return prefs.getString("server_ws_url", BuildConfig.DEFAULT_SERVER_WS_URL);
    }

    private void connectAndStartCall() {
        updateUI(CallState.CONNECTING);
        clearChat();
        String url = getServerUrl();
        Request request = new Request.Builder().url(url).build();
        webSocket = httpClient.newWebSocket(request, new ReceptionistWebSocketListener());
    }

    private void startRecording() {
        if (isMuted.get()) return;
        int bufferSize = AudioRecord.getMinBufferSize(SAMPLE_RATE, CHANNEL_IN, ENCODING);
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
                != PackageManager.PERMISSION_GRANTED) return;

        audioRecord = new AudioRecord(MediaRecorder.AudioSource.MIC,
                SAMPLE_RATE, CHANNEL_IN, ENCODING, bufferSize * 4);

        if (audioRecord.getState() != AudioRecord.STATE_INITIALIZED) {
            showStatus("Microphone unavailable");
            updateUI(CallState.IDLE);
            return;
        }

        isRecording.set(true);
        audioRecord.startRecording();

        executor.submit(() -> {
            byte[] chunk = new byte[2048];
            while (isRecording.get()) {
                int read = audioRecord.read(chunk, 0, chunk.length);
                boolean isPlayingOrEchoing = System.currentTimeMillis() < lastTtsEndTime;
                if (read > 0 && webSocket != null && !isReceivingTts.get() && !isPlayingOrEchoing && !isMuted.get()) {
                    webSocket.send(ByteString.of(chunk, 0, read));
                }
            }
        });

        updateUI(CallState.ACTIVE);
        showStatus("Listening…");
    }

    private void endCall() {
        if (callState == CallState.IDLE) return;
        updateUI(CallState.ENDING);
        showStatus("Call ended");
        stopPulse();
        uiHandler.removeCallbacks(timerTick);

        isRecording.set(false);
        if (audioRecord != null) {
            try { audioRecord.stop(); } catch (Exception ignored) {}
            audioRecord.release();
            audioRecord = null;
        }
        if (currentMediaPlayer != null) {
            try {
                if (currentMediaPlayer.isPlaying()) {
                    currentMediaPlayer.stop();
                }
                currentMediaPlayer.release();
            } catch (Exception ignored) {}
            currentMediaPlayer = null;
        }
        isPlayingTts.set(false);
        if (webSocket != null) {
            webSocket.close(1000, "Call ended by user");
            webSocket = null;
        }
        updateUI(CallState.IDLE);
    }

    private void toggleMute() {
        boolean muted = !isMuted.get();
        isMuted.set(muted);
        uiHandler.post(() -> {
            binding.iconMute.setColorFilter(
                    muted ? Color.parseColor("#EF4444") : Color.parseColor("#8892A4"));
            showStatus(muted ? "Muted" : "Listening…");
        });
    }

    // ── TTS playback ────────────────────────────────────────────────────────

    private void playMp3Bytes(byte[] data) {
        try {
            java.io.File tmpFile = java.io.File.createTempFile("tts_", ".mp3", getCacheDir());
            try (java.io.FileOutputStream fos = new java.io.FileOutputStream(tmpFile)) {
                fos.write(data);
            }
            currentMediaPlayer = new android.media.MediaPlayer();
            currentMediaPlayer.setAudioStreamType(AudioManager.STREAM_MUSIC);
            currentMediaPlayer.setDataSource(tmpFile.getAbsolutePath());
            currentMediaPlayer.prepare();
            int durationMs = currentMediaPlayer.getDuration();
            lastTtsEndTime = System.currentTimeMillis() + durationMs + 800; // 800ms buffer after speech ends
            isPlayingTts.set(true);
            currentMediaPlayer.setOnCompletionListener(player -> {
                isPlayingTts.set(false);
                try { player.release(); } catch (Exception ignored) {}
                if (currentMediaPlayer == player) currentMediaPlayer = null;
                tmpFile.delete();
                if (shouldEndCall.getAndSet(false)) {
                    uiHandler.post(this::endCall);
                } else if (webSocket != null) {
                    uiHandler.post(() -> updateUI(CallState.ACTIVE));
                }
            });
            currentMediaPlayer.start();
            showStatus("Speaking…");
        } catch (IOException e) {
            Log.e(TAG, "MP3 playback failed", e);
        }
    }

    // ── Chat bubble helpers ─────────────────────────────────────────────────

    private void clearChat() {
        uiHandler.post(() -> {
            msgCount = 0;
            // Remove all views except the hint TextView
            int childCount = binding.chatContainer.getChildCount();
            if (childCount > 1) {
                binding.chatContainer.removeViews(1, childCount - 1);
            }
            binding.tvTranscriptHint.setVisibility(View.VISIBLE);
            binding.tvMsgCount.setText("0 messages");
        });
    }

    /**
     * Add a chat bubble.
     * @param text    The message text
     * @param isUser  true = left/blue (user), false = right/dark (AI)
     */
    private void addChatBubble(String text, boolean isUser) {
        uiHandler.post(() -> {
            binding.tvTranscriptHint.setVisibility(View.GONE);
            msgCount++;
            binding.tvMsgCount.setText(msgCount + (msgCount == 1 ? " message" : " messages"));

            // Outer row (for alignment)
            LinearLayout row = new LinearLayout(this);
            row.setOrientation(LinearLayout.VERTICAL);
            LinearLayout.LayoutParams rowParams = new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT);
            rowParams.setMargins(0, 4, 0, 4);
            row.setLayoutParams(rowParams);
            row.setGravity(isUser ? Gravity.START : Gravity.END);

            // Label (You / AI)
            TextView label = new TextView(this);
            label.setText(isUser ? "You" : "AI Receptionist");
            label.setTextColor(Color.parseColor(isUser ? "#3D5A8A" : "#2A3F55"));
            label.setTextSize(9f);
            label.setPadding(isUser ? dp(14) : 0, 0, isUser ? 0 : dp(14), 2);
            label.setGravity(isUser ? Gravity.START : Gravity.END);

            // Bubble
            TextView bubble = new TextView(this);
            bubble.setText(text);
            bubble.setTextColor(Color.parseColor(isUser ? "#A8C8FF" : "#8899B3"));
            bubble.setTextSize(13f);
            bubble.setLineSpacing(0, 1.45f);
            bubble.setBackgroundResource(isUser ? R.drawable.bubble_user : R.drawable.bubble_ai);
            int hPad = dp(14), vPad = dp(10);
            bubble.setPadding(hPad, vPad, hPad, vPad);

            LinearLayout.LayoutParams bubbleParams = new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.WRAP_CONTENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT);
            bubbleParams.setMarginStart(isUser ? 0 : dp(48));
            bubbleParams.setMarginEnd(isUser ? dp(48) : 0);
            bubble.setLayoutParams(bubbleParams);

            row.addView(label);
            row.addView(bubble);

            // Fade-in animation
            AlphaAnimation fadeIn = new AlphaAnimation(0f, 1f);
            fadeIn.setDuration(220);
            row.startAnimation(fadeIn);

            binding.chatContainer.addView(row);
            binding.scrollTranscript.post(() ->
                    binding.scrollTranscript.fullScroll(View.FOCUS_DOWN));
        });
    }

    private View typingIndicator = null;

    private void showTypingIndicator() {
        uiHandler.post(() -> {
            if (typingIndicator != null) return;
            binding.tvTranscriptHint.setVisibility(View.GONE);
            
            LinearLayout row = new LinearLayout(this);
            row.setOrientation(LinearLayout.VERTICAL);
            LinearLayout.LayoutParams rowParams = new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
            rowParams.setMargins(0, 4, 0, 4);
            row.setLayoutParams(rowParams);
            row.setGravity(Gravity.START);

            TextView label = new TextView(this);
            label.setText("You");
            label.setTextColor(Color.parseColor("#3D5A8A"));
            label.setTextSize(9f);
            label.setPadding(dp(14), 0, 0, 2);
            label.setGravity(Gravity.START);

            TextView bubble = new TextView(this);
            bubble.setText("...");
            bubble.setTextColor(Color.parseColor("#A8C8FF"));
            bubble.setTextSize(13f);
            bubble.setBackgroundResource(R.drawable.bubble_user);
            int hPad = dp(14), vPad = dp(10);
            bubble.setPadding(hPad, vPad, hPad, vPad);

            LinearLayout.LayoutParams bubbleParams = new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT);
            bubbleParams.setMarginEnd(dp(48));
            bubble.setLayoutParams(bubbleParams);

            row.addView(label);
            row.addView(bubble);

            AlphaAnimation pulse = new AlphaAnimation(0.4f, 1f);
            pulse.setDuration(400);
            pulse.setRepeatMode(Animation.REVERSE);
            pulse.setRepeatCount(Animation.INFINITE);
            bubble.startAnimation(pulse);

            binding.chatContainer.addView(row);
            binding.scrollTranscript.post(() -> binding.scrollTranscript.fullScroll(View.FOCUS_DOWN));
            typingIndicator = row;
        });
    }

    private void removeTypingIndicator() {
        uiHandler.post(() -> {
            if (typingIndicator != null) {
                binding.chatContainer.removeView(typingIndicator);
                typingIndicator = null;
            }
        });
    }

    private int dp(int dp) {
        return Math.round(dp * getResources().getDisplayMetrics().density);
    }

    // ── UI state machine ────────────────────────────────────────────────────

    private void updateUI(CallState state) {
        callState = state;
        uiHandler.post(() -> {
            switch (state) {
                case IDLE:
                    binding.btnCallBg.setBackgroundResource(R.drawable.btn_call_green);
                    binding.iconCall.setImageResource(android.R.drawable.ic_menu_call);
                    binding.tvConnectionState.setText("Offline");
                    binding.tvConnectionState.setTextColor(Color.parseColor("#8892A4"));
                    binding.statusDot.setBackgroundResource(R.drawable.dot_idle);
                    binding.tvStatus.setText("Tap to connect");
                    binding.tvStatus.setTextColor(Color.parseColor("#5B8DEF"));
                    binding.btnMuteWrap.setVisibility(View.INVISIBLE);
                    binding.btnEndWrap.setVisibility(View.INVISIBLE);
                    binding.tvCallTimer.setVisibility(View.INVISIBLE);
                    callSeconds = 0;
                    binding.tvCallTimer.setText("00:00");
                    stopPulse();
                    break;

                case CONNECTING:
                    binding.tvConnectionState.setText("Connecting…");
                    binding.tvConnectionState.setTextColor(Color.parseColor("#F59E0B"));
                    binding.statusDot.setBackgroundResource(R.drawable.dot_connecting);
                    binding.tvStatus.setText("Connecting to server…");
                    binding.tvStatus.setTextColor(Color.parseColor("#F59E0B"));
                    break;

                case ACTIVE:
                    binding.tvConnectionState.setText("Live");
                    binding.tvConnectionState.setTextColor(Color.parseColor("#22C55E"));
                    binding.statusDot.setBackgroundResource(R.drawable.dot_active);
                    binding.tvStatus.setText("Listening…");
                    binding.tvStatus.setTextColor(Color.parseColor("#22C55E"));
                    binding.btnMuteWrap.setVisibility(View.VISIBLE);
                    binding.btnEndWrap.setVisibility(View.VISIBLE);
                    // Switch call button to active (pulsing) state
                    binding.btnCallBg.setBackgroundResource(R.drawable.btn_call_green);
                    binding.tvCallTimer.setVisibility(View.VISIBLE);
                    startPulse();
                    // Start timer
                    uiHandler.removeCallbacks(timerTick);
                    uiHandler.postDelayed(timerTick, 1000);
                    break;

                case PROCESSING:
                    binding.tvStatus.setText("Processing…");
                    binding.tvStatus.setTextColor(Color.parseColor("#5B8DEF"));
                    break;

                case ENDING:
                    binding.tvConnectionState.setText("Ending…");
                    binding.tvStatus.setText("Ending call…");
                    binding.statusDot.setBackgroundResource(R.drawable.dot_idle);
                    break;
            }
        });
    }

    private void showStatus(String message) {
        uiHandler.post(() -> binding.tvStatus.setText(message));
    }

    // ── WebSocket listener ──────────────────────────────────────────────────

    private class ReceptionistWebSocketListener extends WebSocketListener {

        @Override
        public void onOpen(@NonNull WebSocket ws, @NonNull Response response) {
            startRecording();
        }

        @Override
        public void onMessage(@NonNull WebSocket ws, @NonNull String text) {
            try {
                JSONObject msg = new JSONObject(text);
                String type = msg.optString("type");

                switch (type) {
                    case "speech_started":
                        showTypingIndicator();
                        break;

                    case "transcript":
                        removeTypingIndicator();
                        String transcript = msg.optString("text", "");
                        if (!transcript.isEmpty()) {
                            addChatBubble(transcript, true);
                            showStatus("Processing…");
                            updateUI(CallState.PROCESSING);
                        }
                        break;

                    case "action_result":
                        removeTypingIndicator();
                        String message = msg.optString("message", "");
                        if (msg.optBoolean("end_call", false)) {
                            shouldEndCall.set(true);
                        }
                        if (!message.isEmpty()) {
                            addChatBubble(message, false);
                        }
                        break;

                    case "tts_start":
                        isReceivingTts.set(true);
                        synchronized (ttsBuffer) { ttsBuffer.reset(); }
                        showStatus("Speaking…");
                        break;

                    case "tts_end":
                        isReceivingTts.set(false);
                        byte[] audioData;
                        synchronized (ttsBuffer) { audioData = ttsBuffer.toByteArray(); }
                        if (audioData.length > 0) {
                            final byte[] finalData = audioData;
                            executor.submit(() -> playMp3Bytes(finalData));
                        }
                        break;

                    case "tts_error":
                        isReceivingTts.set(false);
                        updateUI(CallState.ACTIVE);
                        break;

                    case "error":
                        removeTypingIndicator();
                        addChatBubble("⚠ " + msg.optString("message", "Error"), false);
                        showStatus("Error");
                        break;

                    case "processing":
                        // Server received audio and Whisper is running — show status
                        showStatus("Analyzing…");
                        updateUI(CallState.PROCESSING);
                        break;

                    default:
                        Log.d(TAG, "Unhandled: " + type);
                }
            } catch (Exception e) {
                Log.e(TAG, "Message parse error: " + text, e);
            }
        }

        @Override
        public void onMessage(@NonNull WebSocket ws, @NonNull ByteString bytes) {
            if (isReceivingTts.get()) {
                synchronized (ttsBuffer) {
                    try { ttsBuffer.write(bytes.toByteArray()); }
                    catch (IOException e) { Log.e(TAG, "TTS buffer error", e); }
                }
            }
        }

        @Override
        public void onFailure(@NonNull WebSocket ws, @NonNull Throwable t, Response response) {
            Log.e(TAG, "WebSocket failure", t);
            isRecording.set(false);
            if (audioRecord != null) {
                try { audioRecord.stop(); } catch (Exception ignored) {}
                audioRecord.release();
                audioRecord = null;
            }
            updateUI(CallState.IDLE);
            showStatus("Connection failed — tap to retry");
            addChatBubble("⚠ Lost connection: " + t.getMessage(), false);
        }

        @Override
        public void onClosing(@NonNull WebSocket ws, int code, @NonNull String reason) {
            ws.close(1000, null);
        }

        @Override
        public void onClosed(@NonNull WebSocket ws, int code, @NonNull String reason) {
            isRecording.set(false);
            updateUI(CallState.IDLE);
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        isRecording.set(false);
        uiHandler.removeCallbacks(timerTick);
        if (audioRecord != null) { audioRecord.stop(); audioRecord.release(); }
        if (webSocket != null) { webSocket.close(1000, "Activity destroyed"); }
        executor.shutdownNow();
    }
}

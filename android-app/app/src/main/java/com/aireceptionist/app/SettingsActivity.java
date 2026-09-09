package com.aireceptionist.app;

import android.content.SharedPreferences;
import android.os.Bundle;
import android.view.MenuItem;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;

/**
 * Settings screen — allows configuring the backend WebSocket URL.
 * Required for local network testing where the Android phone needs
 * to know the PC's local IP address instead of "localhost".
 */
public class SettingsActivity extends AppCompatActivity {

    private static final String PREFS_NAME = "ai_receptionist_prefs";
    private static final String KEY_WS_URL = "server_ws_url";

    private EditText etServerUrl;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_settings);

        if (getSupportActionBar() != null) {
            getSupportActionBar().setDisplayHomeAsUpEnabled(true);
            getSupportActionBar().setTitle("Server Settings");
        }

        etServerUrl = findViewById(R.id.et_server_url);
        Button btnSave = findViewById(R.id.btn_save_settings);
        Button btnReset = findViewById(R.id.btn_reset_settings);

        // Load current
        SharedPreferences prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        String currentUrl = prefs.getString(KEY_WS_URL, BuildConfig.DEFAULT_SERVER_WS_URL);
        etServerUrl.setText(currentUrl);

        btnSave.setOnClickListener(v -> {
            String url = etServerUrl.getText().toString().trim();
            if (url.isEmpty()) {
                Toast.makeText(this, "URL cannot be empty.", Toast.LENGTH_SHORT).show();
                return;
            }
            if (!url.startsWith("ws://") && !url.startsWith("wss://")) {
                Toast.makeText(this, "URL must start with ws:// or wss://", Toast.LENGTH_SHORT).show();
                return;
            }
            prefs.edit().putString(KEY_WS_URL, url).apply();
            Toast.makeText(this, "Settings saved.", Toast.LENGTH_SHORT).show();
            finish();
        });

        btnReset.setOnClickListener(v -> {
            etServerUrl.setText(BuildConfig.DEFAULT_SERVER_WS_URL);
            prefs.edit().remove(KEY_WS_URL).apply();
            Toast.makeText(this, "Reset to default.", Toast.LENGTH_SHORT).show();
        });
    }

    @Override
    public boolean onOptionsItemSelected(@NonNull MenuItem item) {
        if (item.getItemId() == android.R.id.home) {
            finish();
            return true;
        }
        return super.onOptionsItemSelected(item);
    }
}

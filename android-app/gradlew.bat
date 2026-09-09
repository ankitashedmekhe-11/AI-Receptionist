@rem Gradle wrapper script for Windows (bat)
@rem ##########################################################################
@rem
@rem  Gradle startup script for Windows
@rem
@rem ##########################################################################
@if "%DEBUG%"=="" @echo off
@rem Set local scope for the variables with windows NT shell
setlocal
set DIRNAME=%~dp0
set APP_BASE_NAME=%~n0
set APP_HOME=%DIRNAME%

@rem Find java.exe
if defined JAVA_HOME goto findJavaFromJavaHome
echo Error: JAVA_HOME is not set.
goto fail

:findJavaFromJavaHome
set JAVA_HOME=%JAVA_HOME:"=%
set JAVA_EXE=%JAVA_HOME%/bin/java.exe
if exist "%JAVA_EXE%" goto execute
echo Error: JAVA_HOME is set to an invalid directory.
goto fail

:execute
"%JAVA_EXE%" -classpath "%APP_HOME%\gradle\wrapper\gradle-wrapper.jar" org.gradle.wrapper.GradleWrapperMain %*

:fail
exit /b 1

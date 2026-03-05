package com.voicebridge.app

import android.content.Intent
import android.content.SharedPreferences
import android.media.MediaPlayer
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.text.Editable
import android.text.TextWatcher
import android.util.Log
import android.view.WindowManager
import android.view.inputmethod.InputMethodManager
import android.widget.Button
import android.widget.EditText
import android.widget.ScrollView
import android.widget.TextView
import com.google.android.material.switchmaterial.SwitchMaterial
import androidx.appcompat.app.AppCompatActivity
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.File
import java.io.IOException
import java.util.concurrent.TimeUnit

class MainActivity : AppCompatActivity() {

    private lateinit var serverUrlInput: EditText
    private lateinit var micXInput: EditText
    private lateinit var micYInput: EditText
    private lateinit var transcript: EditText
    private lateinit var statusView: TextView
    private lateinit var a11yStatusView: TextView
    private lateinit var toggleBtn: Button
    private lateinit var a11yBtn: Button
    private lateinit var clearBtn: Button
    private lateinit var clipboardToggle: SwitchMaterial
    private lateinit var modeLabel: TextView
    private lateinit var scrollView: ScrollView
    private lateinit var prefs: SharedPreferences

    private var isActive = false
    private var justSentMessage = false
    private val handler = Handler(Looper.getMainLooper())
    private val client = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(120, TimeUnit.SECONDS)
        .writeTimeout(10, TimeUnit.SECONDS)
        .build()
    private var triggerCheckRunnable: Runnable? = null
    private var micPollRunnable: Runnable? = null
    private var mediaPlayer: MediaPlayer? = null

    private val triggerPattern = Regex("""send\s*message[.!?,\s]*$""", RegexOption.IGNORE_CASE)

    companion object {
        private const val TAG = "VoiceBridge"
        private const val PREFS_NAME = "VoiceBridgePrefs"
        private const val KEY_SERVER_URL = "server_url"
        private const val KEY_MIC_X = "mic_x"
        private const val KEY_MIC_Y = "mic_y"
        private const val KEY_CLIPBOARD_MODE = "clipboard_mode"
        private const val DEFAULT_SERVER_URL = "http://192.168.0.51:5000"
        private const val MIC_POLL_INTERVAL_MS = 2000L
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)

        prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE)

        serverUrlInput = findViewById(R.id.serverUrl)
        micXInput = findViewById(R.id.micX)
        micYInput = findViewById(R.id.micY)
        transcript = findViewById(R.id.transcript)
        statusView = findViewById(R.id.status)
        a11yStatusView = findViewById(R.id.a11yStatus)
        toggleBtn = findViewById(R.id.toggleBtn)
        a11yBtn = findViewById(R.id.a11yBtn)
        clearBtn = findViewById(R.id.clearBtn)
        clipboardToggle = findViewById(R.id.clipboardToggle)
        modeLabel = findViewById(R.id.modeLabel)
        scrollView = findViewById(R.id.scrollView)

        // Load saved settings
        serverUrlInput.setText(prefs.getString(KEY_SERVER_URL, DEFAULT_SERVER_URL))
        clipboardToggle.isChecked = prefs.getBoolean(KEY_CLIPBOARD_MODE, false)
        updateModeLabel()
        val savedX = prefs.getFloat(KEY_MIC_X, -1f)
        val savedY = prefs.getFloat(KEY_MIC_Y, -1f)
        if (savedX >= 0) micXInput.setText(savedX.toInt().toString())
        if (savedY >= 0) micYInput.setText(savedY.toInt().toString())

        toggleBtn.setOnClickListener {
            if (isActive) stopVoiceBridge() else startVoiceBridge()
        }

        a11yBtn.setOnClickListener {
            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
        }

        clearBtn.setOnClickListener {
            transcript.text.clear()
            statusView.text = "Cleared"
        }

        clipboardToggle.setOnCheckedChangeListener { _, isChecked ->
            prefs.edit().putBoolean(KEY_CLIPBOARD_MODE, isChecked).apply()
            updateModeLabel()
        }

        // Watch for text changes — trigger phrase detection
        transcript.addTextChangedListener(object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {}
            override fun afterTextChanged(s: Editable?) {
                if (!isActive || justSentMessage) return
                val text = s?.toString() ?: ""
                if (text.isEmpty()) return

                // Debounce trigger phrase check
                triggerCheckRunnable?.let { handler.removeCallbacks(it) }
                triggerCheckRunnable = Runnable { checkForTrigger() }
                handler.postDelayed(triggerCheckRunnable!!, 1500)

                scrollView.post { scrollView.fullScroll(ScrollView.FOCUS_DOWN) }
            }
        })
    }

    override fun onResume() {
        super.onResume()
        updateA11yStatus()
    }

    private fun updateModeLabel() {
        if (clipboardToggle.isChecked) {
            modeLabel.text = "Mode: Clipboard"
            modeLabel.setTextColor(0xFF64B5F6.toInt())
        } else {
            modeLabel.text = "Mode: Send to CAS"
            modeLabel.setTextColor(0xFFe0e0e0.toInt())
        }
    }

    private fun updateA11yStatus() {
        if (GboardAccessibilityService.isRunning()) {
            a11yStatusView.text = "A11y: ON"
            a11yStatusView.setTextColor(0xFF00FF00.toInt())
        } else {
            a11yStatusView.text = "A11y: OFF"
            a11yStatusView.setTextColor(0xFFFF5555.toInt())
        }
    }

    private fun getMicCoordinates(): Pair<Float, Float>? {
        val xStr = micXInput.text.toString().trim()
        val yStr = micYInput.text.toString().trim()
        if (xStr.isEmpty() || yStr.isEmpty()) return null
        return try {
            Pair(xStr.toFloat(), yStr.toFloat())
        } catch (e: NumberFormatException) {
            null
        }
    }

    private fun saveSettings() {
        val editor = prefs.edit()
        editor.putString(KEY_SERVER_URL, serverUrlInput.text.toString().trim())
        val coords = getMicCoordinates()
        if (coords != null) {
            editor.putFloat(KEY_MIC_X, coords.first)
            editor.putFloat(KEY_MIC_Y, coords.second)
        }
        editor.apply()
    }

    private fun tapMic() {
        val coords = getMicCoordinates() ?: return
        if (GboardAccessibilityService.isRunning()) {
            GboardAccessibilityService.tapMicAt(coords.first, coords.second)
        }
    }

    private fun startVoiceBridge() {
        saveSettings()

        val coords = getMicCoordinates()
        if (coords == null) {
            statusView.text = "Enter mic X and Y coordinates first"
            return
        }
        if (!GboardAccessibilityService.isRunning()) {
            statusView.text = "Enable accessibility service first"
            return
        }

        isActive = true
        justSentMessage = false
        toggleBtn.text = "Stop Listening"
        statusView.text = "Opening keyboard..."

        // Focus the transcript and show keyboard
        transcript.requestFocus()
        val imm = getSystemService(INPUT_METHOD_SERVICE) as InputMethodManager
        imm.showSoftInput(transcript, InputMethodManager.SHOW_IMPLICIT)

        // Wait for keyboard, then start mic and polling
        handler.postDelayed({
            tapMic()
            statusView.text = "Listening via Gboard..."
            startMicPolling()
        }, 1500)
    }

    private fun stopVoiceBridge() {
        isActive = false
        toggleBtn.text = "Start Listening"
        statusView.text = "Stopped"

        stopMicPolling()
        triggerCheckRunnable?.let { handler.removeCallbacks(it) }

        val imm = getSystemService(INPUT_METHOD_SERVICE) as InputMethodManager
        imm.hideSoftInputFromWindow(transcript.windowToken, 0)
    }

    /**
     * Poll Gboard every 2 seconds. If mic is off, tap it.
     */
    private fun startMicPolling() {
        stopMicPolling()
        micPollRunnable = object : Runnable {
            override fun run() {
                if (!isActive) return

                val micActive = GboardAccessibilityService.isMicActive()
                Log.d(TAG, "Mic poll: active=$micActive")

                if (micActive == false) {
                    // Mic is off — restart it
                    Log.d(TAG, "Mic is off — tapping to restart")
                    statusView.text = "Restarting mic..."
                    tapMic()
                    handler.postDelayed({
                        if (isActive) statusView.text = "Listening via Gboard..."
                    }, 1000)
                }

                handler.postDelayed(this, MIC_POLL_INTERVAL_MS)
            }
        }
        // Start polling after a short delay to let the initial tap take effect
        handler.postDelayed(micPollRunnable!!, MIC_POLL_INTERVAL_MS)
    }

    private fun stopMicPolling() {
        micPollRunnable?.let { handler.removeCallbacks(it) }
    }

    private fun checkForTrigger() {
        val text = transcript.text.toString()
        if (triggerPattern.containsMatchIn(text)) {
            val message = text.replace(triggerPattern, "").trim()

            justSentMessage = true
            transcript.text.clear()

            if (message.isNotEmpty()) {
                sendMessage(message)
            }

            // Re-enable after a short delay
            handler.postDelayed({
                justSentMessage = false
            }, 1500)
        }
    }

    private fun sendMessage(message: String) {
        val clipboardMode = clipboardToggle.isChecked
        val serverUrl = serverUrlInput.text.toString().trim()
        val endpoint = if (clipboardMode) "/send-to-clipboard" else "/send-to-cas"
        val label = if (clipboardMode) "Clipboard" else "CAS"

        statusView.text = "Sending to $label..."
        val url = "${serverUrl}${endpoint}"

        val body = message.toRequestBody("text/plain".toMediaType())
        val request = Request.Builder()
            .url(url)
            .post(body)
            .build()

        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                handler.post { statusView.text = "Send failed: ${e.message}" }
            }

            override fun onResponse(call: Call, response: Response) {
                response.use { resp ->
                    val contentType = resp.header("Content-Type") ?: ""
                    if (resp.isSuccessful && contentType.startsWith("audio/")) {
                        // Save audio to temp file and play it
                        try {
                            val tempFile = File(cacheDir, "tts_response.wav")
                            resp.body?.byteStream()?.use { input ->
                                tempFile.outputStream().use { output ->
                                    input.copyTo(output)
                                }
                            }
                            handler.post {
                                statusView.text = "Playing audio..."
                                playAudioFile(tempFile)
                            }
                        } catch (e: Exception) {
                            Log.e(TAG, "Audio save/play error", e)
                            handler.post { statusView.text = "Audio error: ${e.message}" }
                        }
                    } else {
                        handler.post {
                            statusView.text = if (resp.isSuccessful) "Sent to $label!" else "$label error: ${resp.code}"
                        }
                    }
                }
            }
        })
    }

    private fun playAudioFile(file: File) {
        // Release any previous player
        mediaPlayer?.release()

        try {
            mediaPlayer = MediaPlayer().apply {
                setDataSource(file.absolutePath)
                setOnCompletionListener {
                    handler.post { statusView.text = "Audio complete" }
                    it.release()
                    mediaPlayer = null
                }
                setOnErrorListener { mp, what, extra ->
                    Log.e(TAG, "MediaPlayer error: what=$what extra=$extra")
                    handler.post { statusView.text = "Playback error" }
                    mp.release()
                    mediaPlayer = null
                    true
                }
                prepare()
                start()
            }
        } catch (e: Exception) {
            Log.e(TAG, "playAudioFile error", e)
            statusView.text = "Playback error: ${e.message}"
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        stopMicPolling()
        triggerCheckRunnable?.let { handler.removeCallbacks(it) }
        mediaPlayer?.release()
    }
}

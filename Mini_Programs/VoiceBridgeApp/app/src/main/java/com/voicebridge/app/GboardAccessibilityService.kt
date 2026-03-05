package com.voicebridge.app

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.graphics.Path
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo

class GboardAccessibilityService : AccessibilityService() {

    companion object {
        private const val TAG = "VoiceBridgeA11y"
        private const val GBOARD_PACKAGE = "com.google.android.inputmethod.latin"

        private var instance: GboardAccessibilityService? = null

        fun isRunning(): Boolean = instance != null

        fun tapMicAt(x: Float, y: Float) {
            instance?.tapAtCoordinates(x, y)
        }

        /**
         * Check if Gboard's voice mic is currently active.
         * Returns: true = mic ON, false = mic OFF, null = can't determine
         */
        fun isMicActive(): Boolean? {
            return instance?.checkMicState()
        }
    }

    private val handler = Handler(Looper.getMainLooper())

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
        Log.d(TAG, "Accessibility service connected")
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}

    private fun checkMicState(): Boolean? {
        for (window in windows) {
            val root = window.root ?: continue
            val pkg = root.packageName?.toString() ?: ""
            if (pkg != GBOARD_PACKAGE) {
                root.recycle()
                continue
            }

            // Look for the VoiceDictationButton
            val result = findMicState(root)
            root.recycle()
            return result
        }
        return null // Gboard window not found
    }

    private fun findMicState(node: AccessibilityNodeInfo): Boolean? {
        val desc = node.contentDescription?.toString() ?: ""

        // "Stop voice typing" = mic is ON
        // "Use voice typing" = mic is OFF
        if (desc == "Stop voice typing") return true
        if (desc == "Use voice typing") return false

        for (i in 0 until node.childCount) {
            val child = node.getChild(i) ?: continue
            val result = findMicState(child)
            child.recycle()
            if (result != null) return result
        }
        return null
    }

    private fun tapAtCoordinates(x: Float, y: Float) {
        Log.d(TAG, "Double-tapping at ($x, $y)")
        val path1 = Path()
        path1.moveTo(x, y)
        val path2 = Path()
        path2.moveTo(x, y)

        // Two taps in quick succession — double tap keeps Gboard mic active longer (~60s vs ~10s)
        val gesture = GestureDescription.Builder()
            .addStroke(GestureDescription.StrokeDescription(path1, 0, 50))
            .addStroke(GestureDescription.StrokeDescription(path2, 150, 50))
            .build()

        val dispatched = dispatchGesture(gesture, object : GestureResultCallback() {
            override fun onCompleted(gestureDescription: GestureDescription?) {
                Log.d(TAG, "Double-tap completed")
            }
            override fun onCancelled(gestureDescription: GestureDescription?) {
                Log.d(TAG, "Double-tap cancelled")
            }
        }, null)
        Log.d(TAG, "dispatchGesture: $dispatched")
    }

    override fun onInterrupt() {}

    override fun onDestroy() {
        instance = null
        super.onDestroy()
    }
}

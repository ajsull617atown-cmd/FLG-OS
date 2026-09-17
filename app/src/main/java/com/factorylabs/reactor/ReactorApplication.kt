package com.factorylabs.reactor

import android.app.Application
import androidx.appcompat.app.AppCompatDelegate
import android.content.SharedPreferences

class ReactorApplication : Application() {

    companion object {
        const val PREFS_NAME = "reactor_prefs"
        const val KEY_DARK_MODE = "dark_mode"
    }

    override fun onCreate() {
        super.onCreate()
        // Theme switcher - loads saved preference
        val prefs: SharedPreferences = getSharedPreferences(PREFS_NAME, MODE_PRIVATE)
        val isDarkMode = prefs.getBoolean(KEY_DARK_MODE, true)
        if (isDarkMode) {
            AppCompatDelegate.setDefaultNightMode(AppCompatDelegate.MODE_NIGHT_YES)
        } else {
            AppCompatDelegate.setDefaultNightMode(AppCompatDelegate.MODE_NIGHT_NO)
        }
    }

    fun setTheme(isDark: Boolean) {
        val prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE)
        prefs.edit().putBoolean(KEY_DARK_MODE, isDark).apply()
        if (isDark) {
            AppCompatDelegate.setDefaultNightMode(AppCompatDelegate.MODE_NIGHT_YES)
        } else {
            AppCompatDelegate.setDefaultNightMode(AppCompatDelegate.MODE_NIGHT_NO)
        }
    }
}

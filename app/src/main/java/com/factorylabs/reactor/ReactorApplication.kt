package com.factorylabs.reactor

import android.app.Application
import android.content.SharedPreferences
import androidx.appcompat.app.AppCompatDelegate
import androidx.room.Room
import com.factorylabs.reactor.library.ReactorDatabase

class ReactorApplication : Application() {
    companion object {
        const val PREFS_NAME = "reactor_prefs"
        const val KEY_DARK_MODE = "dark_mode"
        lateinit var db: ReactorDatabase
    }

    override fun onCreate() {
        super.onCreate()
        // Room DB - this is what MainActivity uses as ReactorApplication.db
        db = Room.databaseBuilder(
            this,
            ReactorDatabase::class.java,
            "reactor.db"
        ).fallbackToDestructiveMigration().build()

        // Theme switcher - loads saved preference
        val prefs: SharedPreferences = getSharedPreferences(PREFS_NAME, MODE_PRIVATE)
        val isDarkMode = prefs.getBoolean(KEY_DARK_MODE, true)
        if (isDarkMode) {
            AppCompatDelegate.setDefaultNightMode(AppCompatDelegate.MODE_NIGHT_YES)
        } else {
            AppCompatDelegate.setDefaultNightMode(AppCompatDelegate.MODE_NIGHT_NO)
        }
    }
}
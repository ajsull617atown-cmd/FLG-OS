package com.factorylabs.reactor.library

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "games")
data class GameModel(
    @PrimaryKey val packageName: String,
    val label: String,
    val versionName: String = "",
    val versionCode: Long = 0,
    val isSystemApp: Boolean = false,
    val lastUsed: Long = System.currentTimeMillis()
)
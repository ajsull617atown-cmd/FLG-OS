package com.factorylabs.reactor.library

import android.content.Context
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import androidx.room.*

@Dao
interface GameDao {
    @Query("SELECT * FROM games ORDER BY label ASC")
    suspend fun getAll(): List<GameModel>
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(games: List<GameModel>)
    @Query("DELETE FROM games")
    suspend fun clearAll()
}

@Database(entities = [GameModel::class], version = 1, exportSchema = false)
abstract class ReactorDatabase : RoomDatabase() {
    abstract fun gameDao(): GameDao
}

object LauncherService {
    fun getInstalledGames(context: Context): List<GameModel> {
        val pm = context.packageManager
        val packages = pm.getInstalledApplications(PackageManager.GET_META_DATA)
        return packages.mapNotNull { appInfo ->
            try {
                val label = pm.getApplicationLabel(appInfo).toString()
                val isSystem = (appInfo.flags and ApplicationInfo.FLAG_SYSTEM) != 0
                if (label.isNotBlank()) {
                    GameModel(
                        packageName = appInfo.packageName,
                        label = label,
                        isSystemApp = isSystem
                    )
                } else null
            } catch (e: Exception) { null }
        }.sortedBy { it.label.lowercase() }
    }
}
package com.factorylabs.reactor
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.lifecycle.lifecycleScope
import com.factorylabs.reactor.library.*
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val scanner = PackageScanner(this)
        val repo = LibraryRepository(ReactorApplication.db)
        lifecycleScope.launch {
            val installed = scanner.scanInstalledApps()
            repo.syncInstalled(installed)
        }
        setContentView(R.layout.activity_main)
    }
}
package agy.snapshot.host

import android.app.UiModeManager
import android.content.pm.ActivityInfo
import android.content.res.Configuration
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.SystemBarStyle
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.Density

// Hosts the composable under test. Dark mode and orientation are applied to this app only
// (per-app night mode / requestedOrientation), so device settings stay untouched.
class SnapshotActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        val dark = intent.getBooleanExtra("dark", false)
        val fontScale = intent.getFloatExtra("fontScale", 1f)
        requestedOrientation = if (intent.getBooleanExtra("landscape", false))
            ActivityInfo.SCREEN_ORIENTATION_SENSOR_LANDSCAPE else ActivityInfo.SCREEN_ORIENTATION_SENSOR_PORTRAIT
        if (Build.VERSION.SDK_INT >= 31) {
            getSystemService(UiModeManager::class.java).setApplicationNightMode(
                if (dark) UiModeManager.MODE_NIGHT_YES else UiModeManager.MODE_NIGHT_NO)
        }
        super.onCreate(savedInstanceState)
        val isNight = (resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK) == Configuration.UI_MODE_NIGHT_YES
        enableEdgeToEdge(
            statusBarStyle = SystemBarStyle.auto(android.graphics.Color.TRANSPARENT, android.graphics.Color.TRANSPARENT) { isNight },
            navigationBarStyle = SystemBarStyle.auto(android.graphics.Color.TRANSPARENT, android.graphics.Color.TRANSPARENT) { isNight },
        )
        setContent {
            val scheme = when {
                Build.VERSION.SDK_INT >= 31 && isNight -> dynamicDarkColorScheme(this)
                Build.VERSION.SDK_INT >= 31 -> dynamicLightColorScheme(this)
                isNight -> darkColorScheme()
                else -> lightColorScheme()
            }
            val d = LocalDensity.current
            CompositionLocalProvider(LocalDensity provides Density(d.density, d.fontScale * fontScale)) {
                MaterialTheme(colorScheme = scheme) {
                    __ROOT_CALL__
                }
            }
        }
    }
}

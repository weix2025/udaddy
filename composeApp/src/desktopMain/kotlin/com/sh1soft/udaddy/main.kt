package com.sh1soft.udaddy

import androidx.compose.ui.window.Window
import androidx.compose.ui.window.application

fun main() = application {
    Window(
        onCloseRequest = ::exitApplication,
        title = "udaddy",
    ) {
        App()
    }
}
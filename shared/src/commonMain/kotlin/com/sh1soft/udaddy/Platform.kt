package com.sh1soft.udaddy

interface Platform {
    val name: String
}

expect fun getPlatform(): Platform
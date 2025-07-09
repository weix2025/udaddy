package com.sh1soft.daddy

interface Platform {
    val name: String
}

expect fun getPlatform(): Platform
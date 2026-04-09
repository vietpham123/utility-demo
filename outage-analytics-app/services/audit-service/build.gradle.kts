plugins {
    kotlin("jvm") version "1.9.22"
    id("com.github.johnrengelman.shadow") version "8.1.1"
    application
}

repositories {
    mavenCentral()
}

dependencies {
    implementation("io.ktor:ktor-server-core:2.3.7")
    implementation("io.ktor:ktor-server-netty:2.3.7")
    implementation("io.ktor:ktor-server-content-negotiation:2.3.7")
    implementation("io.ktor:ktor-serialization-jackson:2.3.7")
    implementation("ch.qos.logback:logback-classic:1.4.14")
    implementation("org.apache.kafka:kafka-clients:3.6.1")
    implementation("com.fasterxml.jackson.module:jackson-module-kotlin:2.16.1")
    implementation("com.fasterxml.jackson.datatype:jackson-datatype-jsr310:2.16.1")
}

application {
    mainClass.set("com.utility.audit.ApplicationKt")
}

kotlin {
    jvmToolchain(17)
}

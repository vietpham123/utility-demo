package com.genericutility.meterdata;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class MeterDataApplication {
    public static void main(String[] args) {
        SpringApplication.run(MeterDataApplication.class, args);
    }
}

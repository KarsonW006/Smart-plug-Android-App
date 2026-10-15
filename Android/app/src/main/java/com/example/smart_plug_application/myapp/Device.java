package com.example.smart_plug_application.myapp;

// Set class for devices data from database
public class Device {
    private String device_ip;
    private String device_name;

    public Device(String deviceIp, String deviceName) {
        this.device_ip = device_ip;
        this.device_name = device_name;
    }

    public String getDeviceIp() {
        return device_ip;
    }

    public String getDeviceName() {
        return device_name;
    }
}



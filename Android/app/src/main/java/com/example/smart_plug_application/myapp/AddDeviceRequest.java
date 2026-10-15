package com.example.smart_plug_application.myapp;

//For value pass to API call for add device request
public class AddDeviceRequest {
    private String userid;
    private String device_ip;

    public AddDeviceRequest(String userid, String device_ip) {
        this.userid = userid;
        this.device_ip = device_ip;
    }

}

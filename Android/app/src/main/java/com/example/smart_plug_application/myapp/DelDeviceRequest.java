package com.example.smart_plug_application.myapp;

//For value pass to API call for delete device request
public class DelDeviceRequest {
    private String userid;
    private String device_ip;

    public DelDeviceRequest(String userid, String device_ip) {
        this.userid = userid;
        this.device_ip = device_ip;
    }

}

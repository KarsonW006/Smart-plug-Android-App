package com.example.smart_plug_application.myapp;

//For value pass to API call for modify device request
public class ModifyDeviceRequest {
    private String userid;
    private String device_ip;
    private String olddevice_ip;

    public ModifyDeviceRequest(String userid, String device_ip, String olddevice_ip) {
        this.userid = userid;
        this.device_ip = device_ip;
        this.olddevice_ip = olddevice_ip;
    }

}

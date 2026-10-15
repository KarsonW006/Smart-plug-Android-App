package com.example.smart_plug_application.myapp;

//For value pass to API call for add force schedule request
public class AddForceScheduleRequest {
    private String userid;
    private String device_ip;
    private String start_time;
    private String end_time;
    private String run_mode;
    private String status;
    private float threshold;

    public AddForceScheduleRequest(String userid, String device_ip, String start_time, String end_time, String run_mode, String status, float threshold) {
        this.userid = userid;
        this.device_ip = device_ip;
        this.start_time = start_time;
        this.end_time = end_time;
        this.run_mode = run_mode;
        this.status = status;
        this.threshold = threshold;
    }

}

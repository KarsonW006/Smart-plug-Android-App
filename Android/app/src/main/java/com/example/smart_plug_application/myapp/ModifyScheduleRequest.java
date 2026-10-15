package com.example.smart_plug_application.myapp;

//For value pass to API call for modify schedule request
public class ModifyScheduleRequest {
    private String userid;
    private String device_ip;
    private int schedule_id;
    private String start_time;
    private String end_time;
    private String run_mode;
    private float threshold;

    public ModifyScheduleRequest(String userid, String device_ip, int schedule_id, String start_time, String end_time, String run_mode, float threshold) {
        this.userid = userid;
        this.device_ip = device_ip;
        this.schedule_id = schedule_id;
        this.start_time = start_time;
        this.end_time = end_time;
        this.run_mode = run_mode;
        this.threshold = threshold;
    }

}

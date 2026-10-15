package com.example.smart_plug_application.myapp;

//For value pass to API call for change status request
public class ChangeStatusRequest {
    private int schedule_id;
    private String status;

    public ChangeStatusRequest(int schedule_id, String status) {
        this.schedule_id = schedule_id;
        this.status = status;
    }

    // Getters and Setters (if needed)
    public int getScheduleId() {
        return schedule_id;
    }

    public String getStatus() {
        return status;
    }
}
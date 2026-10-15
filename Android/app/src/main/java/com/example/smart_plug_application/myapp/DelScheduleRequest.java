package com.example.smart_plug_application.myapp;

//For value pass to API call for delete schedule request
public class DelScheduleRequest {
    private int schedule_id;

    public DelScheduleRequest(int schedule_id) {
        this.schedule_id = schedule_id;
    }

    // Getter
    public int getScheduleId() {
        return schedule_id;
    }
}

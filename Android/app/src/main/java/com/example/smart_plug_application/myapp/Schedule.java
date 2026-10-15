package com.example.smart_plug_application.myapp;

// Set class for schedule data
public class Schedule {
    private int schedule_id;
    private String start_time;
    private String end_time;
    private String run_mode;
    private String status;
    private float threshold;
    private boolean switchEnabled;

    public Schedule(int scheduleId, String startTime, String endTime, String runMode, String status, float threshold) {
        this.schedule_id = scheduleId;
        this.start_time = startTime;
        this.end_time = end_time;
        this.run_mode = run_mode;
        this.status = status;
        this.threshold = threshold;
    }

    public int getScheduleId() {
        return schedule_id;
    }

    public String getStartTime() {
        return start_time;
    }

    public String getEndTime() {
        return end_time;
    }

    public String getRunMode() {
        return run_mode;
    }

    public String getStatus() {
        return status;
    }

    public float getThreshold() {
        return threshold;
    }

    public boolean isSwitchEnabled() {
        return switchEnabled;
    }

    public void setSwitchEnabled(boolean switchEnabled) {
        this.switchEnabled = switchEnabled;
    }

}

package com.example.smart_plug_application.myapp;


import okhttp3.ResponseBody;
import retrofit2.Call;
import retrofit2.http.Body;
import retrofit2.http.POST;
import retrofit2.http.GET;
import retrofit2.http.Query;


import java.util.List;

public interface ApiService {
    /**
     * Registers a new user.
     * @param user The user details.
     * @return Call<ResponseBody>
     */
    @POST("/register")
    Call<ResponseBody> registerUser(@Body User user);

    /**
     * Logs in a user.
     * @param userLogin The user login details.
     * @return Call<ResponseBody>
     */
    @POST("/login")
    Call<ResponseBody> loginUser(@Body UserLogin userLogin);

    /**
     * Retrieves the price data.
     * @return Call<List<PriceData>>
     */
    @GET("/price_data")
    Call<List<PriceData>> getPriceData();

    /**
     * Changes the user's password.
     * @param changepasword The new password details.
     * @return Call<Void>
     */
    @POST("change_password")
    Call<ResponseBody> changePassword(@Body ChangePassword changepasword);

    /**
     * Updates the notification setting on the server.
     * @param notification The notification setting details.
     * @return Call<Void>
     */
    @POST("server_setting")
    Call<ResponseBody> updateNotificationSetting(@Body Notification notification);

    /**
     * Retrieves the notification setting for a user.
     * @param userid The user's ID.
     * @return Call<List<NotificationSetting>>
     */
    @GET("notify")
    Call<List<NotificationSetting>> retrieveNotificationSetting(@Query("userid") String userid);

    /**
     * Retrieves the schedule for devices for a specific user and device.
     * @param userid The user's ID.
     * @param deviceIp The device IP.
     * @return Call<List<Schedule>>
     */
    @GET("/devices_schedule")
    Call<List<Schedule>> getDeviceSchedules(@Query("userid") String userid, @Query("device_ip") String deviceIp);

    /**
     * Retrieves the list of devices for a specific user.
     * @param userid The user's ID.
     * @return Call<List<Device>>
     */
    @GET("/devices_list")
    Call<List<Device>> getDevicesList(@Query("userid") String userid);

    /**
     * Changes the status of a device.
     * @param request The request body containing the status change details.
     * @return Call<Void>
     */
    @POST("/change_status")
    Call<Void> changeStatus(@Body ChangeStatusRequest request);

    /**
     * Deletes a schedule.
     * @param request The request body containing the schedule details to delete.
     * @return Call<Void>
     */
    @POST("/del_schedule")
    Call<Void> delSchedule(@Body DelScheduleRequest request);

    /**
     * Adds a new device.
     * @param request The request body containing the device details.
     * @return Call<Void>
     */
    @POST("/add_device")
    Call<Void> addDevice(@Body AddDeviceRequest request);

    /**
     * Deletes a device.
     * @param request The request body containing the device details to delete.
     * @return Call<Void>
     */
    @POST("/del_device")
    Call<Void> deleteDevice(@Body DelDeviceRequest request);

    /**
     * Modifies a device's details.
     * @param request The request body containing the device details to modify.
     * @return Call<Void>
     */
    @POST("/modify_device")
    Call<Void> modifyDevice(@Body ModifyDeviceRequest request);

    /**
     * Adds a new schedule.
     * @param request The request body containing the schedule details.
     * @return Call<ResponseBody>
     */
    @POST("/add_schedule")
    Call<ResponseBody> addSchedule(@Body AddScheduleRequest request);

    /**
     * Modifies an existing schedule.
     * @param request The request body containing the schedule details to modify.
     * @return Call<ResponseBody>
     */
    @POST("/modify_schedule")
    Call<ResponseBody> modifySchedule(@Body ModifyScheduleRequest request);

    /**
     * Retrieves the details of a specific schedule.
     * @param scheduleid The ID of the schedule.
     * @return Call<List<Schedule>>
     */
    @GET("/selected_schedule")
    Call<List<Schedule>> getScheduleDetails(@Query("schedule_id") int scheduleid);

    /**
     * Retrieves threshold data.
     * @return Call<List<ThresholdData>>
     */
    @GET("/threshold")
    Call<List<ThresholdData>> getThresholdData();

    /**
     * Retrieves the high price periods.
     * @return Call<List<HighHour>>
     */
    @GET("/high_price_period")
    Call<List<HighHour>> getHighPriceHours();

    /**
     * Retrieves the forecasted prices.
     * @return Call<List<ForecastData>>
     */
    @GET("/forecasted_prices")
    Call<List<ForecastData>> getForecastedPrices();

    /**
     * Retrieves the device_on status for the selected device.
     * @param userid device_ipThe user's ID.
     * @return Call<List<DeviceStatus>>
     */
    @GET("/device_status")
    Call<List<DeviceStatus>> getDeviceStatus(@Query("userid") String userid, @Query("device_ip") String deviceIp);

    /**
     * Adds a new schedule.
     * @param request The request body containing the schedule details.
     * @return Call<ResponseBody>
     */
    @POST("/add_force_schedule")
    Call<ResponseBody> addForceSchedule(@Body AddForceScheduleRequest request);

}



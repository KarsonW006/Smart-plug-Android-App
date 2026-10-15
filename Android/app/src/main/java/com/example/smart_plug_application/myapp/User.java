package com.example.smart_plug_application.myapp;

public class User {
    private String userid; // changed from userID
    private String username; // changed from userName
    private String tapo_password;
    private String password;

    public User(String userid, String username, String tapo_password, String password) {
        this.userid = userid;
        this.username = username;
        this.tapo_password = tapo_password;
        this.password = password;
    }

}
package com.example.smart_plug_application.myapp;

// Set class for change password
public class ChangePassword {
    private String userid; // changed from userID
    private String old_password; // changed from userName
    private String new_password;

    public ChangePassword (String userid, String old_password, String new_password) {
        this.userid = userid;
        this.old_password = old_password;
        this.new_password = new_password;
    }
}

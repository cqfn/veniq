package com.baeldung.constructorsstaticfactorymethods.entities;
import java.time.LocalTime;
import java.util.logging.ConsoleHandler;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.logging.SimpleFormatter;
public class User {
    private static volatile User instance = null;
    private static final Logger LOGGER = Logger.getLogger(User.class.getName());
    private final String name;
    private final String email;
    private final String country;
    public static User createWithDefaultCountry(String name, String email) {
        return new User(name, email, "Argentina");
    }
    public static User createWithLoggedInstantiationTime(String name, String email, String country) {
        ConsoleHandler handler = new ConsoleHandler();
        handler.setLevel(Level.INFO);
        handler.setFormatter(new SimpleFormatter());
        LOGGER.addHandler(handler);
        LOGGER.log(Level.INFO, "Creating User instance at : {0}", LocalTime.now());
        return new User(name, email, country);
    }
}
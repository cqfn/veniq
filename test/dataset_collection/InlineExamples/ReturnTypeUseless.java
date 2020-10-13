import jdk.nashorn.internal.ir.ExpressionStatement;

import java.io.BufferedReader;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;

public class Example {
    private boolean server;
    private boolean active;
    private boolean clientLoaded;

    public Example() {
    }

    public static void main(String[] args) {
        new Example();
    }

    public int invocation() {
        int i = 0;
        System.out.println(0);
        if (i == 0) System.out.println(0);
        while(i < -1) {
            System.out.println(0);
            --i;
        }

        return i;
    }

    public void method_decl() {
        int b = 0;
        System.out.println(b);
        invocation();
        int c = 5;
        ++c;

    }
}

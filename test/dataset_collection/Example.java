package main;


public class Example {
    private boolean server;
    private boolean active;
    private boolean clientLoaded;

    public Net(NetProvider provider) {
    }

    public void method_without_params() {
        closeServer();
        System.out.println(0);
    }

    public int method() {
        method_without_params();
        System.out.println(0);
        return 0;
    }

    public int reset_return_var_decl() {
        int a = closeServer_return();
        System.out.println(0);
        return 0;
    }

    public void method_with_parameters(int a, int b) {
        System.out.println(a);
    }
    public void some_method() {
        System.out.println(1);
        method_with_parameters(1, 2);
    }

    public void overriden_func(int a) {
        ++a;
        System.out.println(a);
    }

    public void overriden_func(float b) {
        System.out.println(b);
    }

    public void invoke_overriden() {
        overriden_func(1);
    }
}

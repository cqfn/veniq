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

    public void closeServer() {
        System.out.println(0);
        System.out.println(0);
        System.out.println(0);
        System.out.println(0);
        System.out.println(0);
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

    public int method_with_return_not_var_decl() {
        int a = closeServer_return();
        System.out.println(0);
        return 0;
    }

    public int closeServer_return() {
        System.out.println(1);
        return 2;
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

    public void overridden_func(int a) {
        ++a;
        System.out.println(a);
    }

    public void overridden_func(float b) {
        System.out.println(b);
    }

    public void invoke_overridden() {
        overridden_func(1);
    }

    public void intersected_var() {
        int s = 0;
        float b = 0;
    }

    public void test_single_stat_in_if() {
        int ghc = 0;
        if(ghc = 0)
            intersected_var();
    }

    public void test_intersected_var_decl() {
        int a = 0;
        ArrayList<String> lst = new ArrayList<>();
        lst.add("e");
        lst.add("q");
        lst.add("z");
        for (String s : lst) {
            System.out.println(s);
            intersected_var();
        }
        int b;
    }

    public void test_not_intersected_var_decl() {
        ArrayList<String> lst = new ArrayList<>();
        lst.add("e");
        for (int i = 0; i < 10; ++i) {
            System.out.println(i);
            intersected_var();
        }
        try (BufferedReader br =
                     new BufferedReader(new FileReader("Example.java"))) {
            if (!lst.isEmpty()) {
                String dfg = new String();

            }
        } catch (IOException e) {
            int try_node;
        }
        int zhmyak;
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
        int a = invocation();
        int c = 5;
        ++c;
    }


    public int severalReturns() {
        int i = 0, j = 0;
        if (i < 0) {
            return 0;
        }

        return 1;
    }

    public void runSeveralReturns() {
        int a = severalReturns();
    }

    @Override
    public CompletableFuture<Void> delete() {
        return CompletableFuture.runAsync(
            () -> {
                try {
                    Files.delete(this.path(1));
                } catch (final IOException iex) {
                    throw new UncheckedIOException(iex);
                }
            },
            this.exec
        );
    }

    public void runDelete() {
        delete();
    }

    public int severalReturnsWithoutMainReturn() {
        int i = 0, j = 0;
        if (i < 0) {
            return 0;
        }
    }

   private Object returnInsideTry() {
    try {
      Object event = events.poll(10, TimeUnit.SECONDS);
      if (event == null) {
        throw new AssertionError("Timed out waiting for event.");
      }
      return event;
    } catch (InterruptedException e) {
      throw new AssertionError(e);
    }
  }

    public void runSeveralReturnsWithoutMainReturn() {
        int a = severalReturnsWithoutMainReturn();
    }
    public void runSeveralReturnsInTry(String payload) {
        Object actual = returnInsideTry();
        assertThat(actual).isEqualTo(new Message(payload));
    }
}

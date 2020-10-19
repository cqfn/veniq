class Test {
    int testMethod(int x, int y, Object o) {
        System.out.println(o);

        while(x > 0) {
            x -= y;
            y++;
            synchronized(o) {
                System.out.println(x);

                {
                    o.foo();
                }

                System.out.println(y);
            }
        }

        for(int i = 0; i < 10; ++i) {
            do {
                o.foo();
                x--;
            } while(x > 0);
        }

        return x;
    }
}
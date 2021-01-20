class InlineWithParams
{
    public void target() {
        int a = 0;
        int b = 0;
        extracted(a, b);
		int e = 0;
        extracted_not_intersected(a, e);
    }
    private void extracted(int a, int b) {
        for (int i = 0; i < 10; i++) { int a = 5; int b = 6; }
        do
        {
            var1 = 2;
        }
        while (var2 == 2);
    }

    public void target_var_not_crossed() {
        int a = 0;
        int b = 0;
        extracted(a, b);
        --a;
        --b;
    }

    public void target_var_crossed() {
        int a = 0;
        int b = 0;
        extracted(a, b);
        --a;
        --b;
        int i = 0;
        --i;
    }

    private void extracted_not_intersected(int g, int c) {
        for (int i = 0; i < 10; i++) { int g = 5; int b = 6; }
        do
        {
            var1 = 2;
        }
        while (var2 == 2);
    }

    private int extracted_return(int a, int b) {
        int u = 0;
        for (int i = 0; i < 10; i++) { int a = 5; int b = 6; }
        do
        {
            var1 = 2;
        }
        while (var2 == 2);

        return u;
    }

    public int target_return() {
        int a = 0;
        int b = 0;
        int e = extracted_return(a, b);
        return e;
    }

    public int return_int() {return 0;}

    public void target_complex() {
        Integer a = 0;
        int b = 0;
        int e = extracted_return(a.intValue(), return_int());
        return e;
    }


}
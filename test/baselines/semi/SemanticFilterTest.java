class Test {
    void noLocalVariablesMethod(int x) {
        foo(x);
        bar(x);
        baz(x);
        someMethod(x);
        otherMethod(x);
    }

    void localUnusedVariables() {
        int x = 0;
        x += 1;
        return 0;
    }

    void localUsedVariable() {
        int x = 0;
        x += 1;
        return x;
    }

    void twoUsedVariables() {
        int x = 0, y = 0;
        return x + y;
    }

    void extractBreak(int x) {
        while(x > 0) {
            break;
        }
    }

    void deepNestedBreak(int x) {
        while(x > 0) {
            if(x == 0) {
                for(int i = 0; i < x; ++i) {
                    break;
                }
            }
        }
    }
}
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

    void tryStatement() {
        int x = 0;
        // there will be no pure try statement in extracted semantic dictionary
        // try statement brings no semantic, but brings blocks, such as main block, catches, etc.
        try {
            x /= 0;
        }
        catch(ArithmeticException e) {

        }
    }
}
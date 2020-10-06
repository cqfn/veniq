class BlockStatementGraphExamples {
    void singleAssertStatement(int x) {
        assert x == 0;
    }

    int singleReturnStatement(int x) {
        return x;
    }

    void singleStatementExpression(int x) {
        x += 1;
    }

    void singleThrowStatement(int x) {
        throw x;
    }

    void singleVariableDeclarationStatement() {
        int x;
    }

    int singleBlockStatement(int x) {
        {
            return x;
        }
    }

    void singleDoStatement(int x) {
        do{
            x--;
        } while(x > 0);
    }

    void singleForStatement(int x) {
        for(int i = 0; i < 10; ++i) {
            x += 1;
        }
    }

    void singleSynchronizeStatement(int x) {
        synchronized(x) {
            x += 1;
        }
    }

    void singleWhileStatement(int x) {
        while(x > 0) {
            x--;
        }
    }

    void cycleWithBreak(int x) {
        while(x > 0) {
            break;
        }
    }

    void cycleWithContinue(int x) {
        while(x > 0) {
            continue;
        }
    }

    void singleIfThenBranch(int x) {
        if(x > 0) {
            x += 1;
        }
    }

    void singleIfTheElseBranches(int x) {
        if(x > 0) {
            x += 1;
        } else {
            x -= 1;
        }
    }

    void severalElseIfBranches(int x) {
        if(x > 0) {
            x += 1;
        } else if(x == 0) {
            x = 0;
        } else {
            x -= 1;
        }
    }

    void switchBranches(int x) {
        switch(x) {
            case 0:
                x = 1;
                System.out.println(x);

            case 1: {
                x = 0;
            }
            System.out.println(x);

            default:
                x = -1;
        }
    }

    void complexExample1(int x) {
        x += 1;

        for(int i = 0; i < x; ++i) {
            x--;
        }

        while(x > 0) {
            x--;
        }

        return x;
    }
}

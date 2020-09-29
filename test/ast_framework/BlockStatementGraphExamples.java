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

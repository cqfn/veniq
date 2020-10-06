package main;


public class Example {
    private boolean server;
    private boolean active;
    private boolean clientLoaded;

    public Net(NetProvider provider) {
    }


    /**
     * Sets the client loaded status, or whether it will recieve normal packets from the server.
     */
    public void setClientLoaded(boolean loaded) {
        clientLoaded = loaded;

        if(loaded) {
            //handle all packets that were skipped while loading
            for(int i = 0; i < packetQueue.size; i++) {
                handleClientReceived(packetQueue.get(i));
            }
        }
        //clear inbound packet queue
        packetQueue.clear();
    }

    public void setClientConnected() {
        active = true;
        server = false;
    }

    /**
     * Connect to an address.
     */
    public void connect(String ip, int port, Runnable success) {
        try {
            if(!active) {
                provider.connectClient(ip, port, success);
                active = true;
                server = false;
            } else {
                throw new IOException("alreadyconnected");
            }
        } catch(IOException e) {
            showError(e);
        }
    }

    /**
     * Host a server at an address.
     */
    public void host(int port) throws IOException {
        provider.hostServer(port);
        active = true;
        server = true;

        Time.runTask(60f, platform::updateRPC);
    }

    /**
     * Closes the server.
     */
    public void closeServer() {
        for(NetConnection con : getConnections()) {
            Call.onKick(con, KickReason.serverClose);
        }

        provider.closeServer();
        server = false;
        active = false;
    }

    /**
     * Closes the server.
     */
    public int closeServer_return() {
        for(NetConnection con : getConnections()) {
            Call.onKick(con, KickReason.serverClose);
        }

        provider.closeServer();
        server = false;
        active = false;

        return 2;
    }

    public void reset() {
        closeServer();
        System.out.println(0);
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
}

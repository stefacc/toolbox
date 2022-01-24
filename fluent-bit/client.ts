import { FluentClient, FluentSocketEvent } from "@fluent-org/logger";

const logger = new FluentClient('SERVICE-1', {
  socket: {
    host: "localhost",
    port: 5170,
    timeout: 5000 // 5 seconds
  }
});

logger.socketOn(FluentSocketEvent.CONNECTED, ()=>{
    console.log("FLUENTBIT","CONNECTED");
})

logger.socketOn(FluentSocketEvent.ERROR, ()=>{
    console.log("FLUENTBIT","ERROR");
})

logger.socketOn(FluentSocketEvent.TIMEOUT, ()=>{
    console.log("FLUENTBIT","TIMEOUT");
})

logger.socketOn(FluentSocketEvent.CLOSE, ()=>{
    console.log("FLUENTBIT","CLOSE");
})

logger.socketOn(FluentSocketEvent.ESTABLISHED, ()=>{
    console.log("FLUENTBIT","ESTABLISHED");
})

export class Logger {

    private static log(message: any): void {
        logger.emit({message: message}, Date.now());
    }
    
}

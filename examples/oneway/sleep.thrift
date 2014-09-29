/**
 * Simple example to show how to use `oneway` with thriftpy.
 */
service Sleep {
    /**
     * Tell the server to sleep!
     */
    oneway void sleep(1: i32 seconds)
}

/* Example of simple PocketSphinx speech segmentation.
 *
 * MIT license (c) 2022, see LICENSE for more information.
 *
 * Author: David Huggins-Daines <dhdaines@gmail.com>
 */
#include <pocketsphinx.h>
#include <signal.h>

static int global_done = 0;
static void
catch_sig(int signum)
{
    global_done = 1;
}

static FILE *
popen_sox(int sample_rate)
{
    char *soxcmd;
    size_t len;
    FILE *sox;
    #define SOXCMD "sox -q -r %d -c 1 -b 16 -e signed-integer -d -t raw -"
    len = snprintf(NULL, 0, SOXCMD, sample_rate);
    if ((soxcmd = malloc(len + 1)) == NULL)
        E_FATAL_SYSTEM("Failed to allocate string");
    if (snprintf(soxcmd, len + 1, SOXCMD, sample_rate) != len)
        E_FATAL_SYSTEM("snprintf() failed");
    if ((sox = popen(soxcmd, "r")) == NULL)
        E_FATAL_SYSTEM("Failed to popen(%s)", soxcmd);
    free(soxcmd);

    return sox;
}

int
main(int argc, char *argv[])
{
    ps_decoder_t *decoder;
    ps_endpointer_t *ep;
    cmd_ln_t *config;
    FILE *sox;
    short *frame;
    size_t frame_size;

    #ifndef MODELDIR
    #define MODELDIR "../model"
    #endif
    if ((config = cmd_ln_init(NULL, ps_args(), TRUE,
                              "-hmm", MODELDIR "/en-us/en-us",
                              "-lm", MODELDIR "/en-us/en-us.lm.bin",
                              "-dict", MODELDIR "/en-us/cmudict-en-us.dict",
                              NULL)) == NULL)
        E_FATAL("Command line parse failed\n");
    ps_default_search_args(config);
    if ((decoder = ps_init(config)) == NULL)
        E_FATAL("PocketSphinx decoder init failed\n");

    if ((ep = ps_endpointer_init(0, 0.0, 0, 0, 0)) == NULL)
        E_FATAL("PocketSphinx endpointer init failed\n");
    sox = popen_sox(ps_endpointer_sample_rate(ep));
    frame_size = ps_endpointer_frame_size(ep);
    if ((frame = malloc(frame_size * sizeof(frame[0]))) == NULL)
        E_FATAL_SYSTEM("Failed to allocate frame");
    if (signal(SIGINT, catch_sig) == SIG_ERR)
        E_FATAL_SYSTEM("Failed to set SIGINT handler");
    while (!global_done) {
        const int16 *speech;
        int prev_in_speech = ps_endpointer_in_speech(ep);
        if (fread(frame, sizeof(frame[0]), frame_size, sox) != frame_size) {
            if (!feof(sox))
                E_ERROR_SYSTEM("Failed to read %d samples", frame_size);
            /* FIXME: Should zero-pad and process, but whatever */
            break;
        }
        speech = ps_endpointer_process(ep, frame);
        if (speech != NULL) {
            const char *hyp;
            if (!prev_in_speech) {
                fprintf(stderr, "Speech start at %.2f\n",
                        ps_endpointer_segment_start(ep));
                ps_start_utt(decoder);
            }
            if (ps_process_raw(decoder, speech, frame_size, FALSE, FALSE) < 0)
                E_FATAL("ps_process_raw() failed\n");
            if ((hyp = ps_get_hyp(decoder, NULL)) != NULL)
                fprintf(stderr, "PARTIAL RESULT: %s\n", hyp);
            if (!ps_endpointer_in_speech(ep)) {
                fprintf(stderr, "Speech end at %.2f\n",
                        ps_endpointer_segment_end(ep));
                ps_end_utt(decoder);
                if ((hyp = ps_get_hyp(decoder, NULL)) != NULL)
                    printf("%s\n", hyp);
            }
        }
    }
    free(frame);
    if (pclose(sox) < 0)
        E_ERROR_SYSTEM("Failed to pclose(sox)");
    ps_endpointer_free(ep);
    ps_free(decoder);
        
    return 0;
}

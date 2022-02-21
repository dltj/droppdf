$(document).ready(function(){
    var player, duration;

    var current_sub;

    var keep_sync = true;

    var scroll_sub_down = true;

    var subtitle_elements = $('.sub');

    var times = [];

    var has_been_started_by_user = false;

    var tag = document.createElement('script');
    tag.src = "https://www.youtube.com/iframe_api";
    var firstScriptTag = document.getElementsByTagName('script')[0];
    firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);


    var captions_url = 'https://youtube.com/api/timedtext?v=' + videoId;
    captions_url += '&fmt=json'
    //captions_url += '&key=yt8'
    captions_url += '&lang=en'

    //captions_url = 'https://www.youtube.com/api/timedtext?v=dP3_ydrmwEQ&asr_langs=de%2Cen%2Ces%2Cfr%2Cid%2Cit%2Cja%2Cko%2Cnl%2Cpt%2Cru%2Ctr%2Cvi&caps=asr&exp=xftt%2Cxctw&xoaf=5&hl=en&ip=0.0.0.0&ipbits=0&expire=1642392085&sparams=ip%2Cipbits%2Cexpire%2Cv%2Casr_langs%2Ccaps%2Cexp%2Cxoaf&signature=DFA56B0B722B9691D658A0ADDEBF0746B2F9A9B6.C6ACEA27C96CF98574368356F075ED0B28B77651&key=yt8&lang=en&name=Default&fmt=json3&xorb=2&xobt=3&xovt=3'
    //

    //captions_url = 'https://www.youtube.com/api/timedtext?v=JRsUz8XQZ_E&asr_langs=de%2Cen%2Ces%2Cfr%2Cid%2Cit%2Cja%2Cko%2Cnl%2Cpt%2Cru%2Ctr%2Cvi&caps=asr&exp=xftt%2Cxctw&xoaf=5&hl=en&ip=0.0.0.0&ipbits=0&expire=1642473038&sparams=ip%2Cipbits%2Cexpire%2Cv%2Casr_langs%2Ccaps%2Cexp%2Cxoaf&signature=52EEB4A84A7AD8C1B7007A9E268FFE6B8F4022FD.30AB7FFD50B3D3D9F84B22807994E040D31E0B37&key=yt8&kind=asr&lang=en&fmt=json3&xorb=2&xobt=3&xovt=3'
    //
    //captions_url = 'https://youtube.com/watch?v=' + videoId;
    //captions_url = $('#video-player-iframe').attr('src');

    //console.log(captions_url);

    //$.get(captions_url, function(rslt) {
        //console.log('ZZ', rslt);
    //});
    setTimeout(function() {
        console.log('XXXX')
        $.ajax({
            method: 'GET',
            url: captions_url,
            crossDomain: true,
            dataType: 'jsonp',
            //dataType: 'html',
        })
        .done(function(rslt) {
            //console.log(rslt);
            console.log();
        })
        .fail(function( x, s, e) {
            console.log('ff');
            console.log(x);
        });
    }, 5000);

    //function getCaptions() {
        //setTimeout(function() {
        //var iframe_html = $('#video-player-iframe').contents().find('html').html();
        //var iframe_html = $('#video-player-iframe').get(0).contentWindow.document.body.innerHTML
        //console.log(iframe_html);
        //}, 5000);
    //};


    function onYouTubeIframeAPIReady() {
        player = new YT.Player('video-player-iframe', {
            playerVars: {
                'autoplay': 1,
                'mute': 1
            },
            events: {
            'onReady': onPlayerReady,
            'onStateChange': onStateChange
            }
        });
        window.player = player;
    };

    function onPlayerReady(event) {
        //binding button (or inline "onclick") don't seem to work initially if 
        //instantiated before player is ready.
        //(sometimes)

        //external play button doesn't work initially if not muted.
        //a recent change in both chrome and firefox apparently.
        //we can start the video (muted) externally, but unmuting caused video to stop
        //player.mute();

        $('#play-button').on('click', function() {
            window.playVideo();
        });

        //getCaptions();
    };

    function onStateChange(event) {
        var st = $('#substart-text');

        if (event.data === YT.PlayerState.PLAYING) {
            $('#play-button').hide();
            $('#play-button-waiting').hide();
            $('#pause-button').show();

            has_been_started_by_user = true;
        };

        if (! has_been_started_by_user) {
            return;
        };

        if ($(st).text().indexOf('Click play') != -1) {
            $(st).text('Beginning of transcript');
        };

        if (event.data === YT.PlayerState.PAUSED) {
            $('#play-button').show();
            $('#pause-button').hide();
        }
    };

    function stopVideo() {
        player.stopVideo();
    };

    function _getCurrentTimeIndex(arr, t) {
        if (arr.length == 1) {
            return window.startTimes.indexOf(arr[0]);
        }

        var mid_index = Math.floor(arr.length / 2);

        if (t >= arr[mid_index]) {
            return _getCurrentTimeIndex(arr.slice(mid_index, arr.length), t);
        }
        return _getCurrentTimeIndex(arr.slice(0, mid_index), t);
    };

    window.player = player;
    window.onYouTubeIframeAPIReady = onYouTubeIframeAPIReady;
    window.onPlayerReady = onPlayerReady;
    window.onStateChange = onStateChange;

    window.playVideo = function() {
        player.playVideo();

        $('#play-button').hide();
        $('#pause-button').show();
    };

    window.pauseVideo = function() {
        player.pauseVideo();

        $('#pause-button').hide();
        $('#play-button').show();
    };

    window.scrollSubs = function(d) {
        if (d == 'down') {
            $('.sub-box').scrollTop(1000000);
        } else {
            $('.sub-box').scrollTop(0);
        };
    };

    window.updatePlayerTime = function(s) {
        player.seekTo(s, true);
    };

    window.toggleSync = function() {
        var b = $('#autoscroll-button');

        keep_sync = ! keep_sync;

        if (keep_sync) {
            $(b)
                .removeClass('button-off')
                .find('i')
                .removeClass('fa-ban')
                .addClass('fa-thumbs-up')

        } else {
            $(b)
                .addClass('button-off')
                .find('i')
                .removeClass('fa-thumbs-up')
                .addClass('fa-ban')
        }
    };

    window.syncScroll = function() {
        var t = player.getCurrentTime();

        if (t) {
            index = _getCurrentTimeIndex(window.startTimes, t);

            el = subtitle_elements[index];

            $('.sub-box').scrollTop(0, 0);

            $('.sub-box').scrollTop($(el).position().top);
        }
    };

    window.searchSubs = function(t, clear) {
        var substart_text = $('#substart-text');
        var subend_text = $('#subend-text');
        var hit_count = 0;
        var match_text = 'matches';

        $('.sub').show();

        $('.search-highlight').each(function(i, v) {
            $(v).before($(v).text());
            $(v).remove();
        });

        //no search, clear results
        if (clear || t.length < 1 || t.replace(/\s\s+/g, ' ') == ' ') {
            $(substart_text).text('Beginning of transcript');
            $(subend_text).text('End of transcript');
            $('#search-input').val('');
            return;
        };

        $(subtitle_elements).each(function(i,sub) {
            var new_content = '';
            var match_sjart, match_stop, pre, post
            var current_startpoint = 0;
            var new_subtext = $('<div class="sub-text"></div>');

            var subtext = $(sub).find('.sub-text').first();
            var text = $(subtext).text();
            var clicktrigger = $(subtext).attr('onclick')

            var r = new RegExp(t, 'ig')

            if (text.search(r) === -1) {

                $(sub).hide();
            }
            else {
                while ((match = r.exec(text)) !== null) {
                    hit_count += 1;
                    match_start = match.index;
                    match_stop = r.lastIndex;

                    pre = text.substring(current_startpoint, match_start)
                    post = text.substring(match_stop)

                    $(new_subtext).append(pre);
                    $(new_subtext).append('<span class="search-highlight">' + match[0] + '</span>');

                    var current_startpoint = match_stop;
                }
                $(new_subtext).append(post);

                $(sub).find('.sub-text')
                    .off('click')
                    .replaceWith(new_subtext);

                $(new_subtext).attr('onclick', clicktrigger);
            }
        });

        if (hit_count == 1) {
            match_text = 'match';
        };

        $(substart_text).text('Beginning of search for "' + t + '" (' + hit_count + ' ' + match_text + ')');
        $(subend_text).text('End of search for "' + t + '" (' + hit_count + ' ' + match_text + ')');
    };

    //pause video when current sub mousedown (for H highlight to prevent scroll leaving sub).
    $('.sub-text').mousedown(function() {
        if (! keep_sync) {
            //if autoscroll isn't enabled, don't pause vid.
            return true;
        };

        //is sub the current one?
        if ($(this).parent().hasClass('highlight')) {
            pauseVideo();
        }
    });

    setInterval(function() {
        if (! keep_sync) {
            $('.highlight').removeClass('highlight');
            return;
        };

        if (! player || ! player.getPlayerState) {
            return;
        };

        if (player.getPlayerState() != 1) {
            return;
        };

        //var ops = player.getOptions('captions')
        //console.log('X', ops.tracklist)

        var t = player.getCurrentTime();

        if (t) {
            index = _getCurrentTimeIndex(window.startTimes, t);

            el = subtitle_elements[index];

            if (el == current_sub) {
                if (! $(el).hasClass('highlight')) {
                    $(el).addClass('highlight');
                }
                return;
            };

            $('.highlight').removeClass('highlight');
            $(el).addClass('highlight');

            if (! keep_sync) {
                return;
            };

            $('.sub-box').scrollTop(0, 0);

            $('.sub-box').scrollTop($(el).position().top);

            current_sub = el;
        };

    }, 1000);


    /* if from a hypothesis share link, advance video time to time of first H highlight */ 
    
    //hypothesis share apparently overwrites location href in code? 
    if (eval('window.location.href').indexOf('via.hypothes.is') != -1) {

        console.log('from share');

        var h_highlights = $('.sub-box').find('.hypothesis-highlight');
        var first_h_highlight, timestamp_el, timstamp_text, spl; 
        var first_h_hl_time = 0;

        if (h_highlights.length > 1) {
            first_h_highlight = h_highlights[0];

            timestamp_el = $(first_h_highlight)
                            .parent()
                            .parent()
                            .find('.sub-time')

            if (timestamp_el) {
                timestamp_text = timestamp_el[0].text();

                if (timestamp_text.length) {
                    spl = timestamp_text.split(':');

                    first_h_hl_time += +spl[0] * 60 * 60
                    first_h_hl_time += +spl[1] * 60
                    first_h_hl_time += +spl[2]

                    updatePlayerTime(first_h_hl_time);

                    syncScroll();
                };
            }

        };
    }

});

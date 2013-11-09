(function($, config){
    var pusher,
        channel,
        pusher_connected = false,
        show_bid_counts = false;

    $.fn.randomize = function(childElem) {
        return this.each(function() {
            var $this = $(this),
                elems = $this.children(childElem),
                itemHeight = $(elems[0]).height();

            elems.css('position', 'relative');
            elems.sort(function() { return Math.random() > 0.4 ? -1 : 1;});
            elems.sort(function() { return Math.random() > 0.5 ? -1 : 1;});

            // add new ordering to <<ordering>> form field
            var ordering = elems.children('input')
                    .map(function() {return $(this).prop('name');})
                    .get().join();
            $('#id_ordering').val(ordering);

            elems.each(function(idx, elm) {
                setTimeout(function() {
                    var pos = $(elm).position().top,
                        idxPos = idx * itemHeight,
                        delta = idxPos - pos;

                    $(elm).animate({top: delta}, 500);

                    if(idx === (elems.length - 1)) {
                        setTimeout(function() {
                            $this.remove(childElem);
                            elems.each(function(){
                                $this.append(this);
                            });
                            elems.css('position', 'static');
                            $('#submit-bids').removeAttr('disabled');
                            $('#items-lead').html('Items');
                        }, 500);
                    }
                }, idx * 500);
            });
        });
    };

    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = $.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    var csrftoken = getCookie('csrftoken');
    $.ajaxSetup({
        crossDomain: false, // obviates need for sameOrigin test
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type)) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    function bid_item($item, bid, self) {
        if(show_bid_counts) {
            if(self === false) {
                var unsaved_bids = $item.data('unsaved-bids');
                if(unsaved_bids === undefined) {
                    $item.data('unsaved-bids', 0);
                }

                if(bid) {
                    unsaved_bids += 1;
                } else {
                    unsaved_bids -= 1;
                }

                $item.data('unsaved-bids', unsaved_bids);
            } else {
                var item_name = $item.prop('name'),
                    event_data = {'from': config['session_id'],
                                  'event': 'item-bid',
                                  'item': item_name,
                                  'bid': bid},
                    post_data = {'data': JSON.stringify(event_data)};

                $.post('/exp/event/' + config['access_token'], post_data)
                    .done(function(data) {
                        if(data.result === false) {
                            console.log('something bad happened');
                            console.log(data);
                        }
                    });
            }
        }
        update_bid_counts();
    }

    function update_bid_counts() {
        if(show_bid_counts) {
            $('#items input').each(function(idx, elm) {
                var saved_bids = $(this).data('saved-bids'),
                    unsaved_bids = $(this).data('unsaved-bids'),
                    total = saved_bids + unsaved_bids,
                    bids_id = '#'+$(this).prop('id')+'_bids';

                $(bids_id).html('Other bids: '+ total);
            });
        }
    }

    $(document).ready(function() {
        pusher = new Pusher(config['pusher_api_key']);
        channel = pusher.subscribe(config['experiment_channel']);

        channel.bind('item-bid', function(data) {
            if(data['from'] !== config['session_id']) {
                bid_item($('#id_'+data['item']), data['bid'], false);
            }
        });

        $('#items input').each(function(idx, elm) {
            var $this = $(this),
                amount = $this.data('amount'),
                badgeLabel = ' <span class="badge">$' + amount + '</span>',
                $label = $this.siblings('label');
            $label.html($label.html() + badgeLabel);

            var saved_bids = $this.data('saved-bids');
            if(saved_bids !== undefined) {
                if(!show_bid_counts) show_bid_counts = true;
                $this.parent().append(' <span id="' + $this.prop('id')
                                      + '_bids' + '"class="badge bid">'
                                      + 'Other Bids: ' + saved_bids + '</span>');
            }
        });


        if(show_bid_counts) {
            var event_data = {'event': 'new-participant'},
                post_data = {'data': JSON.stringify(event_data)};
            $.post('/exp/event/' + config['access_token'],
                   post_data)
                .always(function(data) {
                    var result = JSON.parse(data.responseText);
                    $.each(result['result'], function(item, current_bids) {
                        $('#id_'+item).data('unsaved-bids',
                                            parseInt(current_bids,10));
                    });
                    update_bid_counts();
                });
        }

        $('#goto-form').click(function(ev) {
            $('#instructions').hide();
            $('div.page-header h1').html('Start bidding');
            $('#experiment').show();

            setTimeout(function() {
                $('#items-lead').html('Items (randomizing)');
                $('#items').randomize('li');
            }, 500);
            ev.preventDefault();
        });

        $('#bidding-form').submit(function(ev) {
            var $quota = $('#remaining-quota'),
                quota = parseInt($quota.text(), 10);
            if(quota > 0) {
                alert('You must continue bidding until you finish your quota');
                ev.preventDefault();
            }
        });

        $('#items input').on('click', function(ev) {
            var $target = $(ev.target),
                $quota = $('#remaining-quota'),
                quota = parseInt($quota.text(), 10);

            if($target.prop('checked')) {
                quota = quota - 1;
                $quota.text(quota);
                bid_item($target, true, true);
            } else {
                quota = quota + 1;
                $quota.text(quota);
                bid_item($target, false, true);
            }

            if(quota <= 1) {
                $quota.addClass('quota-low');
            } else {
                $quota.removeClass('quota-low');
            }
        });
    });
})(jQuery, MARKETGAME_CONFIG);

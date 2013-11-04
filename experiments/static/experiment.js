(function($, pusher_api_key, experiment_channel){
    var pusher,
        channel,
        pusher_connected = false,
        show_bid_counts = false;

    function bid_item($item, bid, self) {
        if(show_bid_counts) {
            channel.trigger('item-bid', {
                'item_id': $item.prop('id'),
                'bid': bid
            });

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
            }
        }

        update_bid_counts();
    }

    function update_bid_counts() {
        if(show_bid_counts) {
            $('#items input').each(function(idx, elm) {
                var saved_bids = $(this).data('saved-bids'),
                    unsaved_bids = $(this).data('unsaved-bids');

                $($(this).prop('id') + '_bids').text(saved_bids + unsaved_bids);
            });
        }
    }

    $(document).ready(function() {
        pusher = new Pusher(pusher_api_key);
        channel = pusher.subscribe(experiment_channel);

        channel.bind('item-bid', function(data) {
            console.log('item-bid event');
            console.log(data);
            bid_item($(data.item_id), data.bid, false);
        });

        channel.bind('item-bid-tally', function(data) {
            console.log('item-bid-tally event');
            console.log(data);
            $.each(data.items, function(idx, item) {
                $(item.id).data('unsaved-bids', item.unsaved_bids);
            });
        });

        channel.bind('new-participant', function(data) {
            console.log('new-participant event');
            console.log(data);
            // tally unsaved bids
            var items = $('#items input').map(function() {
                return {
                    id: $(this).prop('id'),
                    unsaved_bids: $(this).data('unsaved-bids')
                };
            });
            channel.trigger('item-bid-tally', {items: items});
        });

        channel.bind('pusher:subscription_succeeded', function() {
            console.log('subscription succeeded');
            pusher_connected = true;
            channel.trigger('new-participant', {});
        });

        $('#items input').each(function(idx, elm) {
            var $this = $(this),
                amount = $this.data('amount'),
                badgeLabel = ' <span class="badge">$' + amount + '</span>',
                $label = $this.siblings('label');
            $label.html($label.html() + badgeLabel);

            var saved_bids = $this.data('saved-bids');
            if(saved_bids) {
                if(!show_bid_counts) show_bid_counts = true;
                $this.parent().append(' <span id="' + $this.prop('id')
                                      + '_bids' + '"class="badge bid">'
                                      + 'Other Bids: ' + saved_bids + '</span>');
            }
        });

        $('#goto-form').click(function(ev) {
            $('#instructions').hide();
            $('div.page-header h1').html('Start bidding');
            $('#experiment').show();
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
})(jQuery, PUSHER_API_KEY, EXPERIMENT_CHANNEL);

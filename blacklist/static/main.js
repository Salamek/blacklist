
function BlockTester()
{
    this.testDone = function(images_cnt, loaded_success_cnt, $blockingStatus)
    {
        var result_url = $blockingStatus.data('result');
        $.ajax({
            type: 'POST',
            url: result_url,
            async: true,
            contentType: 'application/json',
            data: JSON.stringify({
                'tests': images_cnt,
                'success': loaded_success_cnt
            }),
            success: function(images){
                console.log('Block info send');
            },
            error: function() {
                console.log('Failed to send block info');
            }
        });

        $blockingStatus.removeClass('label-info');
        if (images_cnt == loaded_success_cnt)
        {
            $blockingStatus.html('Not blocked (' + loaded_success_cnt + '/' + images_cnt + ')');
            $blockingStatus.addClass('label-success');
        }
        else if (images_cnt / 2 <= loaded_success_cnt)
        {
            $blockingStatus.html('Probably not blocked (' + loaded_success_cnt + '/' + images_cnt + ')');
            $blockingStatus.addClass('label-primary');
        }
        else if (images_cnt / 3 <= loaded_success_cnt)
        {
            $blockingStatus.html('Blocked or network error. (' + loaded_success_cnt + '/' + images_cnt + ')');
            $blockingStatus.addClass('label-warning');
        }
        else
        {
            $blockingStatus.html('BLOCKED! (' + loaded_success_cnt + '/' + images_cnt + ')');
            $blockingStatus.addClass('label-danger');
        }
    };

    this.loadTestImages = function(images, $blockingStatus)
    {
        var that = this;
        var images_cnt = images.length;
        var loaded_cnt = 0;
        var loaded_success_cnt = 0;
        $.each(images, function(k, image_url){
            var image = new Image();
            image.onload = function () {
               loaded_cnt++;
               loaded_success_cnt++;
               if (loaded_cnt >= images_cnt)
               {
                    that.testDone(images_cnt, loaded_success_cnt, $blockingStatus);
               }
            }
            image.onerror = function () {
               loaded_cnt++;
               if (loaded_cnt >= images_cnt)
               {
                    that.testDone(images_cnt, loaded_success_cnt, $blockingStatus);
               }
            }

            image.src = image_url;
        });
    };

    this.test = function($blockingStatus)
    {
        var url = $blockingStatus.data('url');

        var that = this;
        $.ajax({
            type: 'GET',
            url: url,
            async: true,
            success: function(images){
                if (images.length == 0)
                {
                    $blockingStatus.html('Failed to retrieve testing images :(');
                    $blockingStatus.removeClass('label-info');
                    $blockingStatus.addClass('label-warning');
                }
                else
                {
                    that.loadTestImages(images, $blockingStatus);
                }
            },
            error: function() {
                $blockingStatus.html('Failed to retrieve testing images :(');
                $blockingStatus.removeClass('label-info');
                $blockingStatus.addClass('label-warning');
            }
        });
    };
}

$(document).ready(function(){
    $(document).on('click', '[data-toggle="lightbox"]', function(event) {
        event.preventDefault();
        $(this).ekkoLightbox();
    });
    var blockTester = new BlockTester();
    $('.test-enabled .blocking-status').each(function(){
        blockTester.test($(this));
    });

    $('.api-test').click(function(){
        var url = $(this).data('url');

        var $container = $(this).next('.jumbotron');
        if (!$container.length)
        {
            $container = $('<pre class="jumbotron">');
            $(this).after($container);
        }

        $.ajax({
            type: 'GET',
            url: url,
            success: function(data){
                $container.html(JSON.stringify(data, null, 2));
            },
            error: function() {
                $container.html('<div class="alert alert-danger">Failed</div>');
            }
        });
    });

    $('.confirm').click(function(e){
        var message = $(this).data('confirm-message');
        if (!confirm(message))
        {
            e.preventDefault();
        }
    });

    $('.date').each(function(){
        $(this).datetimepicker({
            format: 'DD.MM.YYYY HH:mm'
        });
    });

    $('[data-toggle="popover"]').popover();
    $('.has-error .form-control').first().focus();

    /**
   * Allow anchored tabs
   */
    //Support for urling tabs
    var url = document.location.toString();
    if (url.match('#')) {
        $('.nav-tabs a[href=#'+url.split('#')[1]+']').tab('show') ;
    }

    // Change hash for page-reload
    $('.nav-tabs a').on('shown.bs.tab', function (e) {
        window.location.hash = e.target.hash;
    });
 });

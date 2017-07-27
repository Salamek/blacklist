
$(function () {


    $('.blocking-status').each(function(){
        var url = $(this).data('url');
        var $that = $(this);
        var test_done = function(images_cnt, loaded_success_cnt)
        {
            if (images_cnt == loaded_success_cnt)
            {
                $that.html('Not blocked (' + loaded_success_cnt + '/' + images_cnt + ')');
                $that.removeClass('label-info');
                $that.addClass('label-success');
            }
            else if (images_cnt / 2 <= loaded_success_cnt)
            {
                $that.html('Probably not blocked (' + loaded_success_cnt + '/' + images_cnt + ')');
                $that.removeClass('label-info');
                $that.addClass('label-primary');
            }
            else if (images_cnt / 3 <= loaded_success_cnt)
            {
                $that.html('Blocked or network error. (' + loaded_success_cnt + '/' + images_cnt + ')');
                $that.removeClass('label-info');
                $that.addClass('label-warning');
            }
            else
            {
                $that.html('BLOCKED! (' + loaded_success_cnt + '/' + images_cnt + ')');
                $that.removeClass('label-info');
                $that.addClass('label-danger');
            }
        }
        var image_loader = function (images)
        {
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
                        test_done(images_cnt, loaded_success_cnt);
                   }
                }
                image.onerror = function () {
                   loaded_cnt++;
                   if (loaded_cnt >= images_cnt)
                   {
                        test_done(images_cnt, loaded_success_cnt);
                   }
                }

                image.src = image_url;
            });
        }

        $.ajax({
            type: 'GET',
            url: url,
            success: function(images){
                if (images.length == 0)
                {
                    $that.html('Failed to retrieve testing images :(');
                    $that.removeClass('label-info');
                    $that.addClass('label-warning');
                }
                else
                {
                    image_loader(images);
                }
            },
            error: function() {
                $that.html('Failed to retrieve testing images :(');
                $that.removeClass('label-info');
                $that.addClass('label-warning');
            }
        });
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
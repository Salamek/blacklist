
$(function () {

    $('.blocking-status').each(function(){
        var url = $(this).data('url');

        var $that = $(this);
        $.ajax({
            type: 'HEAD',
            url: url,
            crossDomain: true,
            success: function(){
              $that.html('<div class="label label-success">Not blocked</div>');
            },
            error: function() {
              $that.html('<div class="label label-danger">BLOCKED or CORS :(</div>');
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
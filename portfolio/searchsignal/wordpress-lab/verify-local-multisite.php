<?php
// Read-only CLI acceptance check. Usage: php verify-local-multisite.php /path/to/wp-load.php
if (PHP_SAPI !== 'cli' || empty($argv[1]) || !is_file($argv[1])) {
    fwrite(STDERR, "Supply a local wp-load.php path.\n"); exit(2);
}
require $argv[1];
global $wpdb;
$checks = [];
$check = function ($name, $pass, $evidence) use (&$checks) {
    $checks[] = ['name'=>$name, 'status'=>$pass ? 'pass' : 'fail', 'evidence'=>$evidence];
};
$check('multisite_enabled', is_multisite(), is_multisite());
$check('database_connection', (bool)$wpdb->get_var('SELECT 1'), $wpdb->get_var('SELECT VERSION()'));
$expected = ['/admissions/'=>'MD Admissions Overview', '/research/'=>'Research Programs', '/student-affairs/'=>'Student Support'];
foreach ($expected as $path=>$title) {
    $sites = get_sites(['path'=>$path, 'number'=>1]);
    $check($path.' exists', count($sites)===1, count($sites));
    if (!$sites) continue;
    switch_to_blog($sites[0]->blog_id);
    $pages = get_posts(['post_type'=>'page', 'post_status'=>'publish', 'numberposts'=>-1]);
    $matches = array_values(array_filter($pages, fn($p)=>$p->post_title===$title));
    $check($path.' published_page', count($matches)===1, array_map(fn($p)=>$p->post_title, $pages));
    $check($path.' pretty_permalinks', get_option('permalink_structure')!=='', get_option('permalink_structure'));
    $menus = wp_get_nav_menus();
    $items = array_sum(array_map(fn($m)=>count(wp_get_nav_menu_items($m->term_id) ?: []), $menus));
    $check($path.' menu_items_exist', $items>0, $items);
    $check($path.' database_tables', (bool)$wpdb->get_var("SHOW TABLES LIKE '{$wpdb->posts}'"), $wpdb->posts);
    if ($matches) {
        $url = get_permalink($matches[0]);
        $response = wp_remote_get($url, ['timeout'=>5, 'redirection'=>0]);
        $status = is_wp_error($response) ? 0 : wp_remote_retrieve_response_code($response);
        $body = is_wp_error($response) ? '' : wp_remote_retrieve_body($response);
        $check($path.' page_http', $status===200, ['url'=>$url, 'status'=>$status]);
        $check($path.' page_content', str_contains($body, $title), $title);
    }
    if ($path==='/admissions/') {
        $images = get_posts(['post_type'=>'attachment', 'post_mime_type'=>'image', 'numberposts'=>-1]);
        $alts = array_map(fn($p)=>get_post_meta($p->ID, '_wp_attachment_image_alt', true), $images);
        $check('image_with_alt_text', count(array_filter($alts))>0, $alts);
    }
    restore_current_blog();
}
$failed = count(array_filter($checks, fn($c)=>$c['status']==='fail'));
echo json_encode(['checked_at_utc'=>gmdate('c'), 'scope'=>'Local independent training lab',
    'wordpress_version'=>get_bloginfo('version'), 'checks'=>$checks, 'failed'=>$failed,
    'pending'=>['Rendered navigation inspection', 'Authenticated Network Admin UI inspection',
                'WordPress Playground Blueprint validation', 'SearchSignal crawler integration']],
    JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES).PHP_EOL;
exit($failed ? 1 : 0);

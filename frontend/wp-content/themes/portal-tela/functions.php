<?php
/**
 * Portal Tela Theme Functions
 */

/**
 * Enqueue theme assets (CSS and JS)
 */
function theme_assets() {
    $theme_uri = get_template_directory_uri();
    $theme_dir = get_template_directory();
    
    // Enqueue main CSS
    wp_enqueue_style(
        'theme-style',
        $theme_uri . '/dist/main.css',
        [],
        file_exists($theme_dir . '/dist/main.css') ? filemtime($theme_dir . '/dist/main.css') : '1.0'
    );
    
    // Enqueue Google Fonts (Inter)
    wp_enqueue_style(
        'google-fonts',
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap',
        [],
        null
    );
    
    // Enqueue main JS (with Bootstrap)
    wp_enqueue_script(
        'theme-app',
        $theme_uri . '/dist/app.js',
        [],
        file_exists($theme_dir . '/dist/app.js') ? filemtime($theme_dir . '/dist/app.js') : '1.0',
        true
    );
}
add_action('wp_enqueue_scripts', 'theme_assets');

/**
 * Theme setup
 */
function portal_theme_setup() {
    // Add theme support
    add_theme_support('title-tag');
    add_theme_support('post-thumbnails');
    add_theme_support('html5', [
        'search-form',
        'comment-form',
        'comment-list',
        'gallery',
        'caption',
        'style',
        'script',
    ]);
    add_theme_support('responsive-embeds');
    add_theme_support('custom-logo', [
        'height'      => 50,
        'width'       => 200,
        'flex-height' => true,
        'flex-width'  => true,
    ]);
    
    // Register navigation menus
    register_nav_menus([
        'primary' => 'Menu Principal',
        'footer'  => 'Menu Rodapé',
    ]);
    
    // Set content width
    $GLOBALS['content_width'] = 1200;
}
add_action('after_setup_theme', 'portal_theme_setup');

/**
 * Calculate reading time for a post
 * 
 * @return int Estimated reading time in minutes
 */
function portal_reading_time() {
    $content = get_post_field('post_content', get_the_ID());
    $word_count = str_word_count(strip_tags($content));
    $reading_time = ceil($word_count / 200); // Average reading speed: 200 words/min
    
    return max(1, $reading_time);
}

/**
 * Default menu fallback when no menu is assigned
 */
function portal_default_menu() {
    $categories = get_categories(['number' => 6, 'orderby' => 'count', 'order' => 'DESC']);
    
    echo '<ul class="nav nav-pills">';
    echo '<li class="nav-item"><a href="' . home_url('/') . '" class="nav-link"><i class="bi bi-house me-1"></i>Início</a></li>';
    
    foreach ($categories as $cat) {
        echo '<li class="nav-item">';
        echo '<a href="' . get_category_link($cat->term_id) . '" class="nav-link">' . esc_html($cat->name) . '</a>';
        echo '</li>';
    }
    
    echo '</ul>';
}

/**
 * Bootstrap Nav Walker for WordPress menus
 */
class Bootstrap_Nav_Walker extends Walker_Nav_Menu {
    
    public function start_lvl(&$output, $depth = 0, $args = null) {
        $indent = str_repeat("\t", $depth);
        $output .= "\n$indent<ul class=\"dropdown-menu\">\n";
    }
    
    public function start_el(&$output, $item, $depth = 0, $args = null, $id = 0) {
        $indent = ($depth) ? str_repeat("\t", $depth) : '';
        
        $classes = empty($item->classes) ? [] : (array) $item->classes;
        $classes[] = 'nav-item';
        
        // Check if item has children
        $has_children = in_array('menu-item-has-children', $classes);
        
        if ($has_children && $depth === 0) {
            $classes[] = 'dropdown';
        }
        
        $class_names = join(' ', apply_filters('nav_menu_css_class', array_filter($classes), $item, $args, $depth));
        $class_names = $class_names ? ' class="' . esc_attr($class_names) . '"' : '';
        
        $output .= $indent . '<li' . $class_names . '>';
        
        $atts = [];
        $atts['title']  = !empty($item->attr_title) ? $item->attr_title : '';
        $atts['target'] = !empty($item->target) ? $item->target : '';
        $atts['rel']    = !empty($item->xfn) ? $item->xfn : '';
        $atts['href']   = !empty($item->url) ? $item->url : '';
        
        // Add Bootstrap classes
        if ($depth === 0) {
            $atts['class'] = 'nav-link';
            if ($has_children) {
                $atts['class'] .= ' dropdown-toggle';
                $atts['role'] = 'button';
                $atts['data-bs-toggle'] = 'dropdown';
                $atts['aria-expanded'] = 'false';
            }
        } else {
            $atts['class'] = 'dropdown-item';
        }
        
        // Active state
        if (in_array('current-menu-item', $classes)) {
            $atts['class'] .= ' active';
            $atts['aria-current'] = 'page';
        }
        
        $atts = apply_filters('nav_menu_link_attributes', $atts, $item, $args, $depth);
        
        $attributes = '';
        foreach ($atts as $attr => $value) {
            if (!empty($value)) {
                $value = ('href' === $attr) ? esc_url($value) : esc_attr($value);
                $attributes .= ' ' . $attr . '="' . $value . '"';
            }
        }
        
        $title = apply_filters('the_title', $item->title, $item->ID);
        $title = apply_filters('nav_menu_item_title', $title, $item, $args, $depth);
        
        $item_output = $args->before ?? '';
        $item_output .= '<a' . $attributes . '>';
        $item_output .= ($args->link_before ?? '') . $title . ($args->link_after ?? '');
        $item_output .= '</a>';
        $item_output .= $args->after ?? '';
        
        $output .= apply_filters('walker_nav_menu_start_el', $item_output, $item, $depth, $args);
    }
}

/**
 * Add custom body classes
 */
function portal_body_classes($classes) {
    if (is_single()) {
        $classes[] = 'single-post-page';
    }
    
    return $classes;
}
add_filter('body_class', 'portal_body_classes');

/**
 * Customize excerpt length
 */
function portal_excerpt_length($length) {
    return 30;
}
add_filter('excerpt_length', 'portal_excerpt_length');

/**
 * Customize excerpt more text
 */
function portal_excerpt_more($more) {
    return '...';
}
add_filter('excerpt_more', 'portal_excerpt_more');

/**
 * Add additional image sizes
 */
add_image_size('post-thumbnail-large', 1200, 630, true);
add_image_size('post-thumbnail-medium', 600, 400, true);
add_image_size('post-thumbnail-small', 300, 200, true);
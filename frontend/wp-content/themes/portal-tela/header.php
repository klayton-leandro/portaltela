<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo('charset'); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="<?php bloginfo('description'); ?>">
    <?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<!-- Top Bar -->
<div class="top-bar bg-dark text-white py-2 d-none d-md-block">
    <div class="container">
        <div class="row align-items-center">
            <div class="col-md-6">
                <div class="d-flex align-items-center gap-4 small">
                    <span>
                        <i class="bi bi-calendar3 me-1"></i>
                        <?php echo date_i18n('l, d \d\e F \d\e Y'); ?>
                    </span>
                    <span class="text-white-50">|</span>
                    <span>
                        <i class="bi bi-clock me-1"></i>
                        <span id="live-time"><?php echo date_i18n('H:i'); ?></span>
                    </span>
                </div>
            </div>
            <div class="col-md-6 text-end">
                <div class="d-flex align-items-center justify-content-end gap-3 small">
                    <a href="#" class="text-white-50 text-decoration-none hover-white">
                        <i class="bi bi-facebook"></i>
                    </a>
                    <a href="#" class="text-white-50 text-decoration-none hover-white">
                        <i class="bi bi-twitter-x"></i>
                    </a>
                    <a href="#" class="text-white-50 text-decoration-none hover-white">
                        <i class="bi bi-instagram"></i>
                    </a>
                    <a href="#" class="text-white-50 text-decoration-none hover-white">
                        <i class="bi bi-youtube"></i>
                    </a>
                    <span class="text-white-50">|</span>
                    <a href="<?php bloginfo('rss2_url'); ?>" class="text-white-50 text-decoration-none hover-white">
                        <i class="bi bi-rss me-1"></i>RSS
                    </a>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Main Header -->
<header class="main-header bg-white py-3 border-bottom">
    <div class="container">
        <div class="row align-items-center">
            <!-- Logo -->
            <div class="col-lg-4 col-md-6 col-8">
                <a href="<?php echo esc_url(home_url('/')); ?>" class="text-decoration-none d-flex align-items-center">
                    <div class="logo-icon bg-primary text-white rounded-3 d-flex align-items-center justify-content-center me-3" 
                         style="width: 50px; height: 50px;">
                        <i class="fs-4">P</i>
                    </div>
                    <div>
                        <h1 class="h4 mb-0 text-dark fw-bold">Notícias</h1>
                        <small class="text-muted d-none d-sm-block"><?php bloginfo('description'); ?></small>
                    </div>
                </a>
            </div>
            
            <!-- Search (Desktop) -->
            <div class="col-lg-4 d-none d-lg-block">
                <form action="<?php echo home_url('/'); ?>" method="get" class="search-form">
                    <div class="input-group">
                        <input type="search" 
                               name="s" 
                               class="form-control border-0 bg-light" 
                               placeholder="Buscar notícias..."
                               value="<?php echo get_search_query(); ?>"
                               aria-label="Buscar">
                        <button class="btn btn-primary px-4" type="submit">
                            <i class="bi bi-search"></i>
                        </button>
                    </div>
                </form>
            </div>
            
            <!-- Weather/Info or Mobile Toggle -->
            <div class="col-lg-4 col-md-6 col-4 text-end">
                <div class="d-none d-lg-flex align-items-center justify-content-end gap-3">
                    <div class="text-end">
                        <small class="text-muted d-block">Bem-vindo ao</small>
                    </div>
                    <div class="vr"></div>
                    <a href="#" class="btn btn-outline-primary btn-sm">
                        <i class="bi bi-bell me-1"></i>
                        Newsletter
                    </a>
                </div>
                
                <!-- Mobile Toggle -->
                <button class="btn btn-primary d-lg-none" type="button" data-bs-toggle="offcanvas" data-bs-target="#mobileMenu">
                    <i class="bi bi-list fs-4"></i>
                </button>
            </div>
        </div>
    </div>
</header>

<main id="main-content">


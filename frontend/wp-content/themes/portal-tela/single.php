<?php get_header(); ?>

<?php while (have_posts()) : the_post(); ?>

<!-- Hero Section com Imagem Destacada -->
<header class="post-hero position-relative">
    <?php if (has_post_thumbnail()) : ?>
        <div class="post-hero-image">
            <?php the_post_thumbnail('full', ['class' => 'w-100 h-100 object-fit-cover']); ?>
            <div class="post-hero-overlay"></div>
        </div>
    <?php else : ?>
        <div class="post-hero-gradient"></div>
    <?php endif; ?>
    
    <div class="container position-relative z-1">
        <div class="row justify-content-center">
            <div class="col-lg-10 text-center py-5">
                <!-- Categorias -->
                <div class="post-categories mb-3">
                    <?php
                    $categories = get_the_category();
                    foreach (array_slice($categories, 0, 3) as $category) :
                    ?>
                        <a href="<?php echo esc_url(get_category_link($category->term_id)); ?>" 
                           class="badge bg-primary text-decoration-none me-1">
                            <?php echo esc_html($category->name); ?>
                        </a>
                    <?php endforeach; ?>
                </div>
                
                <!-- Título -->
                <h1 class="post-title display-4 fw-bold text-white mb-4">
                    <?php the_title(); ?>
                </h1>
                
                <!-- Meta informações -->
                <div class="post-meta d-flex flex-wrap justify-content-center gap-4 text-white-50">
                    <span class="d-flex align-items-center">
                        <i class="bi bi-person-circle me-2"></i>
                        <?php the_author(); ?>
                    </span>
                    <span class="d-flex align-items-center">
                        <i class="bi bi-calendar3 me-2"></i>
                        <time datetime="<?php echo get_the_date('c'); ?>">
                            <?php echo get_the_date('d \d\e F \d\e Y'); ?>
                        </time>
                    </span>
                    <span class="d-flex align-items-center">
                        <i class="bi bi-clock me-2"></i>
                        <?php echo portal_reading_time(); ?> min de leitura
                    </span>
                </div>
            </div>
        </div>
    </div>
</header>

<!-- Conteúdo Principal -->
<article class="post-content py-5">
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-lg-8">
                
                <!-- Excerpt / Lead -->
                <?php if (has_excerpt()) : ?>
                    <div class="post-excerpt lead text-muted border-start border-primary border-4 ps-4 mb-5">
                        <?php the_excerpt(); ?>
                    </div>
                <?php endif; ?>
                
                <!-- Conteúdo do Post -->
                <div class="post-body">
                    <?php the_content(); ?>
                </div>
                
                <!-- Tags -->
                <?php
                $tags = get_the_tags();
                if ($tags) :
                ?>
                    <div class="post-tags mt-5 pt-4 border-top">
                        <div class="d-flex flex-wrap align-items-center gap-2">
                            <span class="text-muted me-2">
                                <i class="bi bi-tags me-1"></i>Tags:
                            </span>
                            <?php foreach ($tags as $tag) : ?>
                                <a href="<?php echo esc_url(get_tag_link($tag->term_id)); ?>" 
                                   class="badge bg-light text-dark text-decoration-none">
                                    <?php echo esc_html($tag->name); ?>
                                </a>
                            <?php endforeach; ?>
                        </div>
                    </div>
                <?php endif; ?>
                
                <!-- Compartilhamento -->
                <div class="post-share mt-4 p-4 bg-light rounded-3">
                    <div class="d-flex flex-wrap align-items-center justify-content-between gap-3">
                        <span class="fw-semibold">
                            <i class="bi bi-share me-2"></i>Compartilhe esta notícia:
                        </span>
                        <div class="share-buttons d-flex gap-2">
                            <a href="https://www.facebook.com/sharer/sharer.php?u=<?php echo urlencode(get_permalink()); ?>" 
                               target="_blank" rel="noopener" 
                               class="btn btn-sm btn-outline-primary" 
                               aria-label="Compartilhar no Facebook">
                                <i class="bi bi-facebook"></i>
                            </a>
                            <a href="https://twitter.com/intent/tweet?url=<?php echo urlencode(get_permalink()); ?>&text=<?php echo urlencode(get_the_title()); ?>" 
                               target="_blank" rel="noopener" 
                               class="btn btn-sm btn-outline-dark" 
                               aria-label="Compartilhar no Twitter">
                                <i class="bi bi-twitter-x"></i>
                            </a>
                            <a href="https://api.whatsapp.com/send?text=<?php echo urlencode(get_the_title() . ' ' . get_permalink()); ?>" 
                               target="_blank" rel="noopener" 
                               class="btn btn-sm btn-outline-success" 
                               aria-label="Compartilhar no WhatsApp">
                                <i class="bi bi-whatsapp"></i>
                            </a>
                            <a href="https://www.linkedin.com/shareArticle?mini=true&url=<?php echo urlencode(get_permalink()); ?>&title=<?php echo urlencode(get_the_title()); ?>" 
                               target="_blank" rel="noopener" 
                               class="btn btn-sm btn-outline-primary" 
                               aria-label="Compartilhar no LinkedIn">
                                <i class="bi bi-linkedin"></i>
                            </a>
                            <button type="button" 
                                    class="btn btn-sm btn-outline-secondary copy-link-btn" 
                                    data-url="<?php echo esc_url(get_permalink()); ?>"
                                    aria-label="Copiar link">
                                <i class="bi bi-link-45deg"></i>
                            </button>
                        </div>
                    </div>
                </div>
                
                <!-- Box do Autor -->
                <div class="post-author-box mt-5 p-4 bg-white rounded-3 shadow-sm border">
                    <div class="d-flex gap-4">
                        <div class="author-avatar flex-shrink-0">
                            <?php echo get_avatar(get_the_author_meta('ID'), 80, '', '', ['class' => 'rounded-circle']); ?>
                        </div>
                        <div class="author-info">
                            <h5 class="mb-1">
                                <a href="<?php echo esc_url(get_author_posts_url(get_the_author_meta('ID'))); ?>" 
                                   class="text-decoration-none text-dark">
                                    <?php the_author(); ?>
                                </a>
                            </h5>
                            <p class="text-muted mb-0 small">
                                <?php echo get_the_author_meta('description') ?: 'Autor do ' . get_bloginfo('name'); ?>
                            </p>
                        </div>
                    </div>
                </div>
                
            </div>
        </div>
    </div>
</article>

<!-- Posts Relacionados -->
<?php
$related_posts = new WP_Query([
    'posts_per_page' => 3,
    'post__not_in'   => [get_the_ID()],
    'category__in'   => wp_get_post_categories(get_the_ID()),
    'orderby'        => 'rand',
]);

if ($related_posts->have_posts()) :
?>
<section class="related-posts bg-light py-5">
    <div class="container">
        <h3 class="text-center mb-4">
            <i class="bi bi-newspaper me-2"></i>Notícias Relacionadas
        </h3>
        <div class="row g-4">
            <?php while ($related_posts->have_posts()) : $related_posts->the_post(); ?>
                <div class="col-md-4">
                    <article class="card h-100 border-0 shadow-sm hover-lift">
                        <?php if (has_post_thumbnail()) : ?>
                            <a href="<?php the_permalink(); ?>">
                                <?php the_post_thumbnail('medium', ['class' => 'card-img-top']); ?>
                            </a>
                        <?php endif; ?>
                        <div class="card-body">
                            <div class="text-muted small mb-2">
                                <i class="bi bi-calendar3 me-1"></i>
                                <?php echo get_the_date('d/m/Y'); ?>
                            </div>
                            <h5 class="card-title">
                                <a href="<?php the_permalink(); ?>" class="text-decoration-none text-dark stretched-link">
                                    <?php the_title(); ?>
                                </a>
                            </h5>
                        </div>
                    </article>
                </div>
            <?php endwhile; ?>
        </div>
    </div>
</section>
<?php
wp_reset_postdata();
endif;
?>

<?php endwhile; ?>

<?php get_footer(); ?>

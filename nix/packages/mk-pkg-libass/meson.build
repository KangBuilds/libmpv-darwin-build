# https://mesonbuild.com/External-Project-module.html

project('libass', 'c')

mod = import('unstable-external_project')
cross_prefix = meson.get_cross_property('cross_prefix')

p = mod.add_project('configure',
    env : {
        'AR': cross_prefix + '/ar',
        'NM': cross_prefix + '/nm',
        'RANLIB': cross_prefix + '/ranlib',
    },
    configure_options : [
        '--prefix=@PREFIX@',
        '--disable-static',
        '--enable-fast-install',
        '--disable-dependency-tracking',
        '--disable-test',
        '--disable-compare',
        '--disable-profile',
        '--disable-fuzz',
        '--disable-fontconfig',
        '--disable-directwrite',
        '--enable-coretext',
        '--disable-libunibreak',
        '--disable-require-system-font-provider',
        '--disable-asm',
        '--disable-large-tiles',
        '--with-pic',
        '--with-aix-soname=aix',
        '--without-gnu-ld',
    ],
    verbose: true,
)

libass_dep = p.dependency('libass')
meson.override_dependency('libass', libass_dep)

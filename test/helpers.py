# -*- coding: utf-8 -*-
#
import matplotlib2tikz

import imagehash
import matplotlib
import matplotlib.pyplot as plt
import os
from PIL import Image
import shutil
import subprocess
import tempfile


class Phash(object):
    def __init__(self, fig):
        # convert to tikz file
        _, tmp_base = tempfile.mkstemp()
        tikz_file = tmp_base + '_tikz.tex'
        matplotlib2tikz.save(
            tikz_file,
            figurewidth='7.5cm'
            )

        # test other height specs
        matplotlib2tikz.save(
            tikz_file + '.height',
            figureheight='7.5cm',
            show_info=True,
            strict=True,
            )

        # save reference figure
        mpl_reference = tmp_base + '_reference.pdf'
        plt.savefig(mpl_reference)

        # close figure
        plt.close(fig)

        # create a latex wrapper for the tikz
        wrapper = '''\\documentclass{standalone}
    \\usepackage[utf8]{inputenc}
    \\usepackage{pgfplots}
    \\usepgfplotslibrary{groupplots}
    \\usetikzlibrary{shapes.arrows}
    \\pgfplotsset{compat=newest}
    \\begin{document}
    \\input{%s}
    \\end{document}''' % tikz_file
        tex_file = tmp_base + '.tex'
        with open(tex_file, 'w') as f:
            f.write(wrapper)

        # change into the directory of the TeX file
        os.chdir(os.path.dirname(tex_file))

        # compile the output to pdf
        try:
            tex_out = subprocess.check_output(
                # use pdflatex for now until travis features a more modern
                # lualatex
                ['pdflatex', '--interaction=nonstopmode', tex_file],
                stderr=subprocess.STDOUT
                )
        except subprocess.CalledProcessError as e:
            print('Command output:')
            print('=' * 70)
            print(e.output)
            print('=' * 70)
            if 'DISPLAY' not in os.environ:
                cmd = ['curl', '-sT', tikz_file, 'chunk.io']
                out = subprocess.check_output(
                    cmd,
                    stderr=subprocess.STDOUT
                    )
                print('Uploaded TikZ file to %s' % out.decode('utf-8'))
            raise

        pdf_file = tmp_base + '.pdf'

        # Convert PDF to PNG.
        ptp_out = subprocess.check_output(
            [
                'pdftoppm', '-rx', '600', '-ry', '600', '-png',
                pdf_file, tmp_base
            ],
            stderr=subprocess.STDOUT
            )
        png_file = tmp_base + '-1.png'

        self.phash = imagehash.phash(Image.open(png_file)).__str__()
        self.png_file = png_file
        self.pdf_file = pdf_file
        self.tex_out = tex_out
        self.ptp_out = ptp_out
        self.mpl_reference = mpl_reference
        self.tikz_file = tikz_file
        return

    def get_details(self):
        # Copy pdf_file in test directory
        shutil.copy(self.pdf_file, os.path.dirname(os.path.abspath(__file__)))

        print('Output file: %s' % self.png_file)
        print('computed pHash:  %s' % self.phash)
        # Compute the Hamming distance between the two 64-bit numbers
        # hamming_dist = \
        #     bin(int(phash, 16) ^ int(reference_phash, 16)).count('1')
        # print('reference pHash: %s' % reference_phash)
        # print(
        #     'Hamming distance: %s (out of %s)' %
        #     (hamming_dist, 4 * len(phash))
        #     )
        print('pdflatex output:')
        print(self.tex_out.decode('utf-8'))

        print('pdftoppm output:')
        print(self.ptp_out.decode('utf-8'))

        if 'DISPLAY' not in os.environ:
            # upload to chunk.io if we're on a headless client
            out = subprocess.check_output(
                ['curl', '-sT', self.mpl_reference, 'chunk.io'],
                stderr=subprocess.STDOUT
                )
            print(
                'Uploaded reference matplotlib PDF file to %s' %
                out.decode('utf-8')
                )

            out = subprocess.check_output(
                ['curl', '-sT', self.tikz_file, 'chunk.io'],
                stderr=subprocess.STDOUT
                )
            print('Uploaded TikZ file to %s' % out.decode('utf-8'))

            out = subprocess.check_output(
                ['curl', '-sT', self.pdf_file, 'chunk.io'],
                stderr=subprocess.STDOUT
                )
            print('Uploaded output PDF file to %s' % out.decode('utf-8'))

            out = subprocess.check_output(
                ['curl', '-sT', self.png_file, 'chunk.io'],
                stderr=subprocess.STDOUT
                )
            print('Uploaded output PNG file to %s' % out.decode('utf-8'))
        return


def print_tree(obj, indent=''):
    '''Recursively prints the tree structure of the matplotlib object.
    '''
    if isinstance(obj, matplotlib.text.Text):
        print(indent, type(obj).__name__, '("%s")' % obj.get_text())
    else:
        print(indent, type(obj).__name__)

    for child in obj.get_children():
        print_tree(child, indent + '   ')
    return